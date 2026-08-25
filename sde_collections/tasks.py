# /sde_collections/tasks.py

import logging

from django.apps import apps
from django.conf import settings
from django.db import transaction

from config import celery_app
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)

from .indexing.dispatch import run_index_task
from .indexing.export import export_curated_to_s3
from .indexing.run_status import fetch_run_status, fetch_validation_report
from .models.delta_url import DumpUrl
from .models.indexing import IndexDispatch
from .scraping.s3_results import fetch_documents, fetch_summary, results_ready
from .scraping.ssm_dispatch import send_job_to_crawler
from .utils.slack_utils import (
    notify_status_change,
    send_detailed_import_notification,
    send_indexing_validation_report,
    send_slack_message,
)

logger = logging.getLogger(__name__)

# Statuses a collection can hold while a crawl is in flight on the *workflow* path. A
# scrape/ingest failure may only rewrite workflow_status when it is one of these; on the
# re-scrape path (reindexing_status) the live workflow status — typically PROD_* — is
# left alone.
SCRAPE_FLOW_STATUSES = (
    WorkflowStatusChoices.READY_FOR_ENGINEERING,
    WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
    WorkflowStatusChoices.SCRAPING_SUCCESSFUL,
)


def _mark_scrape_failed(collection, reason):
    """Record a scrape/ingest failure without clobbering a status outside the scrape flow.

    Uses a queryset .update() (so no post_save side effects fire) and posts the mapped
    Slack message itself. Outside the scrape flow only an alert is sent.
    """
    Collection = apps.get_model("sde_collections", "Collection")
    old_status = Collection.objects.filter(id=collection.id).values_list("workflow_status", flat=True).first()
    if old_status in SCRAPE_FLOW_STATUSES:
        Collection.objects.filter(id=collection.id).update(workflow_status=WorkflowStatusChoices.SCRAPING_FAILED)
        notify_status_change(collection.name, collection.id, old_status, WorkflowStatusChoices.SCRAPING_FAILED)
        return
    # Re-scrape path: keep the live workflow status, and clear the reindexing request so
    # the poller stops re-enqueueing the same failed run every 5 minutes.
    logger.error("Re-scrape of %s failed (%s); workflow status left unchanged", collection.config_folder, reason)
    Collection.objects.filter(id=collection.id).update(reindexing_status=ReindexingStatusChoices.REINDEXING_NOT_NEEDED)
    try:
        send_slack_message(
            f"Alert: re-scrape of '{collection.name}' failed ({reason}). "
            f"Workflow status was left unchanged; set Re-Indexing Needed again to retry."
        )
    except Exception as e:
        logger.warning("Error sending Slack message for %s: %s", collection.name, e)


@celery_app.task()
def sync_with_production_webapp():
    Collection = apps.get_model("sde_collections", "Collection")

    for collection in Collection.objects.all():
        collection.sync_with_production_webapp()


@celery_app.task()
def resolve_title_pattern(title_pattern_id):
    TitlePattern = apps.get_model("sde_collections", "TitlePattern")
    title_pattern = TitlePattern.objects.get(id=title_pattern_id)
    title_pattern.apply()


@celery_app.task()
def migrate_dump_to_delta_and_handle_status_transistions(collection_id):
    """Task to migrate DumpUrls to DeltaUrls after classification is complete"""
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)

    initial_workflow_status = collection.workflow_status
    initial_reindexing_status = collection.reindexing_status
    dump_count = collection.dump_urls.count()
    curated_count = collection.curated_urls.count()

    # Migrate dump URLs to delta URLs
    collection.migrate_dump_to_delta()

    # Update statuses if needed
    collection.refresh_from_db()

    # Check workflow status transition
    pre_workflow_statuses = [
        WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
        WorkflowStatusChoices.READY_FOR_ENGINEERING,
        WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
        WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV,
        WorkflowStatusChoices.SCRAPING_SUCCESSFUL,
    ]
    if initial_workflow_status in pre_workflow_statuses:
        collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        collection.save()

    # Check reindexing status transition
    if initial_reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV:
        collection.reindexing_status = ReindexingStatusChoices.REINDEXING_READY_FOR_CURATION
        collection.save()

    # Post the ingest summary for the scrape-ingest paths (WORKFLOW.md step 11).
    # Sent from here, not the ingest task, because the delta counts only exist
    # after migration.
    if initial_workflow_status == WorkflowStatusChoices.SCRAPING_SUCCESSFUL or (
        initial_reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
    ):
        try:
            send_detailed_import_notification(
                collection_name=collection.name,
                total_server_count=dump_count,
                curated_count=curated_count,
                dump_count=dump_count,
                delta_count=collection.delta_urls.count(),
                marked_for_deletion_count=collection.delta_urls.filter(to_delete=True).count(),
            )
        except Exception as e:
            logger.warning("Error sending ingest summary to Slack for %s: %s", collection.config_folder, e)

    return f"Successfully migrated DumpUrls to DeltaUrls for collection {collection.name}."


@celery_app.task()
def dispatch_scrape_job(collection_id):
    """Send a scrape job for the collection to the crawl4ai crawler via SSM.

    Triggered by READY_FOR_ENGINEERING and REINDEXING_NEEDED_ON_DEV (and manually via
    the dispatch_scrape management command). On success records a ScrapeDispatch row —
    the poller's freshness reference and the stall timeout's start time. On failure
    sets SCRAPING_FAILED and records nothing; the error never raises out of the task.
    """
    Collection = apps.get_model("sde_collections", "Collection")
    ScrapeDispatch = apps.get_model("sde_collections", "ScrapeDispatch")
    collection = Collection.objects.get(id=collection_id)

    try:
        command_id = send_job_to_crawler(collection)
    except Exception as e:
        logger.exception("Scrape dispatch failed for %s: %s", collection.config_folder, e)
        _mark_scrape_failed(collection, f"dispatch error: {e}")
        return None

    ScrapeDispatch.objects.create(collection=collection, ssm_command_id=command_id)
    return command_id


@celery_app.task()
def poll_scrape_jobs():
    """Beat task (every 5 min, gated on SCRAPE_POLL_ENABLED): find collections awaiting
    crawl results and enqueue ingest for those whose run has completed.

    Scans READY_FOR_ENGINEERING and ENGINEERING_IN_PROGRESS (engineers flip to the latter
    while a crawl runs — a collection must not strand there), plus the re-scrape path
    (reindexing_status == REINDEXING_NEEDED_ON_DEV). Completion means a summary object
    fresher than the latest ScrapeDispatch; with no fresh summary past the stall timeout
    the run is declared dead.
    """
    from datetime import timedelta

    from django.utils import timezone

    Collection = apps.get_model("sde_collections", "Collection")

    waiting = Collection.objects.filter(
        workflow_status__in=[
            WorkflowStatusChoices.READY_FOR_ENGINEERING,
            WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
        ]
    ) | Collection.objects.filter(reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV)

    stall_timeout = timedelta(hours=settings.SCRAPE_STALL_TIMEOUT_HOURS)
    now = timezone.now()
    enqueued = 0

    for collection in waiting.distinct():
        dispatch = collection.scrape_dispatches.first()  # Meta.ordering: latest first
        if dispatch is None:
            continue  # never dispatched — nothing to poll against

        try:
            summary = results_ready(collection.config_folder, dispatch.dispatched_at)
        except Exception as e:
            logger.error("Error checking S3 results for %s: %s", collection.config_folder, e)
            continue

        if summary is not None:
            ingest_scraped_collection.delay(collection.id)
            enqueued += 1
        elif now - dispatch.dispatched_at > stall_timeout:
            logger.error(
                "Scrape stalled for %s: no fresh results %sh after dispatch",
                collection.config_folder,
                settings.SCRAPE_STALL_TIMEOUT_HOURS,
            )
            _mark_scrape_failed(collection, f"no results {settings.SCRAPE_STALL_TIMEOUT_HOURS}h after dispatch")

    return f"Enqueued ingest for {enqueued} collection(s)."


PROD_STATUS_FOR_QC_STATUS = {
    WorkflowStatusChoices.QUALITY_CHECK_PERFECT: WorkflowStatusChoices.PROD_PERFECT,
    WorkflowStatusChoices.QUALITY_CHECK_MINOR: WorkflowStatusChoices.PROD_MINOR,
}


def _mint_run_id():
    import uuid

    from django.utils import timezone

    return f"{timezone.now().strftime('%Y-%m-%dT%H-%M-%SZ')}-{uuid.uuid4().hex[:6]}"


def _dispatch_index_run(collection_id, target, in_flight_status, failed_status):
    """Shared body of the two indexing hand-off tasks: mint run_id -> export (manifest
    last) -> RunTask -> record IndexDispatch -> set the in-flight status. Never indexes
    in-process; failure lands on the target's failed status and never raises."""
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)
    run_id = _mint_run_id()
    previous_status = collection.workflow_status

    try:
        document_count = export_curated_to_s3(collection, target, run_id)
        if document_count == 0:
            raise ValueError("curated set is empty — nothing to index")
        task_arn = run_index_task(collection, target, run_id)
    except Exception as e:
        logger.exception("Index dispatch (%s) failed for %s: %s", target, collection.config_folder, e)
        collection.workflow_status = failed_status
        collection.save()
        return None

    IndexDispatch.objects.create(
        collection=collection,
        run_id=run_id,
        target=target,
        task_arn=task_arn,
        previous_workflow_status=previous_status,
    )
    collection.workflow_status = in_flight_status
    collection.save()
    logger.info(
        "Dispatched %s index run %s for %s (%s documents)", target, run_id, collection.config_folder, document_count
    )
    return run_id


@celery_app.task()
def index_collection_to_test(collection_id):
    """Hand a curated collection to the WEB_COSMOS indexer, test target."""
    return _dispatch_index_run(
        collection_id,
        target=IndexDispatch.TARGET_TEST,
        in_flight_status=WorkflowStatusChoices.TEST_INDEXING,
        failed_status=WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
    )


@celery_app.task()
def index_collection_to_prod(collection_id):
    """Hand a QC-passed collection to the WEB_COSMOS indexer, prod target."""
    return _dispatch_index_run(
        collection_id,
        target=IndexDispatch.TARGET_PROD,
        in_flight_status=WorkflowStatusChoices.PRODUCTION_INDEXING,
        failed_status=WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    )


@celery_app.task()
def poll_index_runs():
    """Beat task (every 2 min, gated on INDEX_POLL_ENABLED): resolve in-flight index runs
    by polling S3 status.json — never ecs.describe_tasks.

    Mapping: succeeded+test -> stay TEST_INDEXING and post the validation report to Slack
    (curator sets QC from it); succeeded+prod -> PROD_PERFECT/PROD_MINOR mirroring the QC
    status the run entered with; failed, unknown state, or stall timeout -> the target's
    INDEXING_FAILED status. run_id namespacing means an old run's status.json can never
    satisfy a newer dispatch.
    """
    from datetime import timedelta

    from django.utils import timezone

    Collection = apps.get_model("sde_collections", "Collection")

    failed_status_for_target = {
        IndexDispatch.TARGET_TEST: WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
        IndexDispatch.TARGET_PROD: WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    }
    stall_timeout = timedelta(hours=settings.INDEX_STALL_TIMEOUT_HOURS)
    now = timezone.now()
    resolved = 0

    in_flight = Collection.objects.filter(
        workflow_status__in=[
            WorkflowStatusChoices.TEST_INDEXING,
            WorkflowStatusChoices.PRODUCTION_INDEXING,
        ]
    )
    for collection in in_flight:
        dispatch = collection.index_dispatches.filter(completed_at__isnull=True).first()
        if dispatch is None:
            continue  # nothing open to poll (e.g. status set by hand)

        try:
            status = fetch_run_status(collection.config_folder, dispatch.run_id)
        except Exception as e:
            logger.error("Error checking index run for %s: %s", collection.config_folder, e)
            continue

        if status is None:
            if now - dispatch.dispatched_at > stall_timeout:
                logger.error("Index run stalled for %s (run %s)", collection.config_folder, dispatch.run_id)
                collection.workflow_status = failed_status_for_target[dispatch.target]
                collection.save()
                dispatch.completed_at = now
                dispatch.save()
                resolved += 1
            continue

        state = status.get("state")
        if state == "succeeded":
            if dispatch.target == IndexDispatch.TARGET_TEST:
                # Collection stays at TEST_INDEXING; the curator sets QC from the report.
                try:
                    validation = fetch_validation_report(collection.config_folder, dispatch.run_id)
                    send_indexing_validation_report(collection.name, dispatch.run_id, validation)
                except Exception as e:
                    logger.warning("Error posting validation report for %s: %s", collection.config_folder, e)
            else:
                # Explicit map only: a prod run entered from anything other than a QC
                # status (e.g. a manual re-dispatch) stays at PRODUCTION_INDEXING for a
                # human to resolve rather than being silently promoted.
                mirrored = PROD_STATUS_FOR_QC_STATUS.get(dispatch.previous_workflow_status)
                if mirrored is None:
                    logger.warning(
                        "Prod index run %s for %s succeeded but entered from status %r; "
                        "leaving PRODUCTION_INDEXING for manual resolution",
                        dispatch.run_id,
                        collection.config_folder,
                        dispatch.previous_workflow_status,
                    )
                    try:
                        send_slack_message(
                            f"Prod indexing of '{collection.name}' succeeded (run {dispatch.run_id}) but the run "
                            f"was not started from a QC status. Please set the final Prod status by hand."
                        )
                    except Exception as e:
                        logger.warning("Error sending Slack message for %s: %s", collection.name, e)
                else:
                    collection.workflow_status = mirrored
                    collection.save()
        else:
            # "failed" and any unknown state are both failures — needs_confirmation is
            # reserved for future two-phase deletion and must not read as success.
            logger.error(
                "Index run for %s (run %s) ended state=%r error=%r",
                collection.config_folder,
                dispatch.run_id,
                state,
                status.get("error"),
            )
            collection.workflow_status = failed_status_for_target[dispatch.target]
            collection.save()

        dispatch.completed_at = now
        dispatch.save()
        resolved += 1

    return f"Resolved {resolved} index run(s)."


@celery_app.task(soft_time_limit=600)
def ingest_scraped_collection(collection_id, claim=True):
    """Ingest completed crawl results from S3 into DumpUrls (replaces fetch_full_text).

    The status transition IS the claim, executed as a compare-and-swap before any write:
    ingest can outrun the 5-minute poll, and BaseUrl.url is globally unique, so two
    concurrent ingests would die on IntegrityError mid-write. claim=False (manual
    ingest_scrape_results command) skips the CAS — explicit operator intent — but the
    delete-then-write body keeps the replay idempotent.
    """
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)
    cid = collection.config_folder

    if claim:
        dispatch = collection.scrape_dispatches.first()
        summary = results_ready(cid, dispatch.dispatched_at if dispatch else None)
    else:
        found = fetch_summary(cid)
        summary = found[0] if found else None
    if summary is None:
        return f"No (fresh) results for {cid}; nothing ingested."

    # Zero-document completion is a failure: without this, an empty crawl would
    # "succeed" and silently publish an empty collection.
    if summary.get("documents_scraped", 0) == 0:
        _mark_scrape_failed(collection, "crawl completed with 0 documents")
        return f"Scrape of {cid} completed with 0 documents; marked Scraping Failed."

    if claim:
        old_status = collection.workflow_status
        claimed = Collection.objects.filter(
            id=collection_id,
            workflow_status__in=[
                WorkflowStatusChoices.READY_FOR_ENGINEERING,
                WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
            ],
        ).update(workflow_status=WorkflowStatusChoices.SCRAPING_SUCCESSFUL)
        if claimed:
            # .update() bypasses post_save, so post the transition message ourselves.
            notify_status_change(collection.name, collection.id, old_status, WorkflowStatusChoices.SCRAPING_SUCCESSFUL)
        else:
            # Workflow path not claimable — try the re-scrape path.
            claimed = Collection.objects.filter(
                id=collection_id,
                reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV,
            ).update(reindexing_status=ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV)
        if claimed == 0:
            return f"{cid} already claimed by another ingest; exiting."

    try:
        documents = _dedupe_by_url(fetch_documents(cid), cid)
        with transaction.atomic():
            deleted_count, _ = DumpUrl.objects.filter(collection=collection).delete()
            batch_size = 500
            for start in range(0, len(documents), batch_size):
                DumpUrl.objects.bulk_create(
                    [
                        DumpUrl(
                            url=document["url"],
                            collection=collection,
                            scraped_title=document.get("title") or "",
                            scraped_text=document.get("full_text") or "",
                        )
                        for document in documents[start : start + batch_size]  # noqa: E203
                    ]
                )
        logger.info("Ingested %s documents for %s (replaced %s).", len(documents), cid, deleted_count)

        collection.refresh_from_db()
        collection.queue_necessary_classifications()
        return f"Ingested {len(documents)} documents for {cid}."
    except Exception as e:
        # Never leave a claimed collection stuck in SCRAPING_SUCCESSFUL with no DumpUrls.
        # On the re-scrape path the live workflow status is left alone (see _mark_scrape_failed).
        logger.exception("Ingest failed for %s: %s", cid, e)
        _mark_scrape_failed(collection, f"ingest error: {e}")
        return None


def _dedupe_by_url(documents, cid):
    """Drop repeated URLs within one crawl output (first occurrence wins).

    BaseUrl.url is unique, so a single duplicate would otherwise abort the whole
    bulk_create inside the atomic block.
    """
    seen = set()
    unique = []
    for document in documents:
        url = document.get("url")
        if not url or url in seen:
            continue
        seen.add(url)
        unique.append(document)
    dropped = len(documents) - len(unique)
    if dropped:
        logger.warning("Dropped %s duplicate/blank-URL documents from crawl output for %s", dropped, cid)
    return unique

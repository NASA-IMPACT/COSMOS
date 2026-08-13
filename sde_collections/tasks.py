# /sde_collections/tasks.py

from django.apps import apps
from django.conf import settings
from django.db import transaction

from config import celery_app
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)

from .models.delta_url import DumpUrl
from .scraping.s3_results import fetch_documents, fetch_summary, results_ready
from .scraping.ssm_dispatch import send_job_to_crawler
from .utils.slack_utils import send_detailed_import_notification


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
            print(f"Error sending ingest summary to Slack: {e}")

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
        print(f"Scrape dispatch failed for {collection.config_folder}: {e}")
        collection.workflow_status = WorkflowStatusChoices.SCRAPING_FAILED
        collection.save()
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
            print(f"Error checking S3 results for {collection.config_folder}: {e}")
            continue

        if summary is not None:
            ingest_scraped_collection.delay(collection.id)
            enqueued += 1
        elif now - dispatch.dispatched_at > stall_timeout:
            print(
                f"Scrape stalled for {collection.config_folder}: no fresh results "
                f"{settings.SCRAPE_STALL_TIMEOUT_HOURS}h after dispatch"
            )
            collection.workflow_status = WorkflowStatusChoices.SCRAPING_FAILED
            collection.save()

    return f"Enqueued ingest for {enqueued} collection(s)."


@celery_app.task()
def index_collection_to_test(collection_id):
    """P5 stub — the event-trigger seam for the WEB_COSMOS indexing pipeline
    (sde-api-scrapers, branch web-indexing). P7 fills this in: mint a run_id, export the
    curated set to S3 (documents.jsonl + manifest.json, manifest written last), assume
    the dispatch role, and ecs:RunTask with a command override. Never indexes in-process.
    """
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)
    collection.workflow_status = WorkflowStatusChoices.TEST_INDEXING
    collection.save()
    print(f"[P5 stub] Test indexing recorded for {collection.config_folder}; dispatch lands in P7.")
    return f"Test indexing started for {collection.config_folder}"


@celery_app.task()
def index_collection_to_prod(collection_id):
    """P5 stub — prod counterpart of index_collection_to_test; see its docstring."""
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)
    collection.workflow_status = WorkflowStatusChoices.PRODUCTION_INDEXING
    collection.save()
    print(f"[P5 stub] Production indexing recorded for {collection.config_folder}; dispatch lands in P7.")
    return f"Production indexing started for {collection.config_folder}"


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
        Collection.objects.filter(id=collection_id).update(
            workflow_status=WorkflowStatusChoices.SCRAPING_FAILED
        )
        return f"Scrape of {cid} completed with 0 documents; marked Scraping Failed."

    if claim:
        claimed = Collection.objects.filter(
            id=collection_id,
            workflow_status__in=[
                WorkflowStatusChoices.READY_FOR_ENGINEERING,
                WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
            ],
        ).update(workflow_status=WorkflowStatusChoices.SCRAPING_SUCCESSFUL)
        if claimed == 0:
            # Workflow path not claimable — try the re-scrape path.
            claimed = Collection.objects.filter(
                id=collection_id,
                reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV,
            ).update(reindexing_status=ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV)
        if claimed == 0:
            return f"{cid} already claimed by another ingest; exiting."

    try:
        documents = fetch_documents(cid)
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
        print(f"Ingested {len(documents)} documents for {cid} (replaced {deleted_count}).")

        collection.refresh_from_db()
        collection.queue_necessary_classifications()
        return f"Ingested {len(documents)} documents for {cid}."
    except Exception as e:
        # Never leave a claimed collection stuck in SCRAPING_SUCCESSFUL with no DumpUrls.
        print(f"Ingest failed for {cid}: {e}")
        Collection.objects.filter(id=collection_id).update(
            workflow_status=WorkflowStatusChoices.SCRAPING_FAILED
        )
        return None

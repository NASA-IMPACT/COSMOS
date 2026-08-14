# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_ingest.py

import io
import json
from datetime import datetime, timedelta
from datetime import timezone as dt_timezone
from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError
from django.test import override_settings
from django.utils import timezone

from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.delta_url import DumpUrl
from sde_collections.models.scraper_config import ScrapeDispatch
from sde_collections.scraping.s3_results import (
    fetch_documents,
    fetch_summary,
    results_ready,
)
from sde_collections.tasks import (
    ingest_scraped_collection,
    migrate_dump_to_delta_and_handle_status_transistions,
    poll_scrape_jobs,
)
from sde_collections.tests.factories import CollectionFactory


def make_documents(count, seed="https://example.nasa.gov/"):
    """Fixture matching the crawler's exact 7-field document shape."""
    return [
        {
            "url": f"{seed}page-{i}",
            "title": f"Page {i}",
            "full_text": f"Full text of page {i}",
            "content_type": "text/html",
            "seed": seed,
            "host": "example.nasa.gov",
            "depth": 1,
        }
        for i in range(count)
    ]


def make_summary(documents_scraped):
    return {"documents_scraped": documents_scraped, "failures_logged": 0, "seed": "https://example.nasa.gov/"}


def backdate_dispatch(dispatch, hours):
    ScrapeDispatch.objects.filter(id=dispatch.id).update(
        dispatched_at=timezone.now() - timedelta(hours=hours)
    )


@pytest.mark.django_db
class TestIngestScrapedCollection:
    @patch("sde_collections.tasks.migrate_dump_to_delta_and_handle_status_transistions.delay")
    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.results_ready")
    def test_happy_path_creates_dump_urls_and_claims_status(self, mock_ready, mock_docs, mock_migrate):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(3)
        mock_docs.return_value = make_documents(3)

        ingest_scraped_collection(collection.id)

        dumps = DumpUrl.objects.filter(collection=collection).order_by("url")
        assert dumps.count() == 3
        assert dumps[0].scraped_title == "Page 0"
        assert dumps[0].scraped_text == "Full text of page 0"
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.SCRAPING_SUCCESSFUL
        mock_migrate.assert_called_once_with(collection.id)

    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.results_ready")
    def test_zero_documents_marks_scraping_failed(self, mock_ready, mock_docs):
        """A zero-page crawl otherwise 'succeeds' and silently publishes an empty collection."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(0)

        ingest_scraped_collection(collection.id)

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.SCRAPING_FAILED
        assert not DumpUrl.objects.filter(collection=collection).exists()
        mock_docs.assert_not_called()

    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.results_ready")
    def test_concurrent_claim_exits_without_touching_dump_urls(self, mock_ready, mock_docs):
        """CAS returns 0 for an already-claimed collection — second ingest must exit."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.SCRAPING_SUCCESSFUL)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        DumpUrl.objects.create(collection=collection, url="https://example.nasa.gov/existing")
        mock_ready.return_value = make_summary(3)

        result = ingest_scraped_collection(collection.id)

        assert "already claimed" in result
        assert DumpUrl.objects.filter(collection=collection).count() == 1
        mock_docs.assert_not_called()

    @patch("sde_collections.tasks.migrate_dump_to_delta_and_handle_status_transistions.delay")
    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.fetch_summary")
    def test_manual_ingest_is_idempotent(self, mock_summary, mock_docs, mock_migrate):
        """Re-running manual ingest yields N (not 2N) DumpUrls — delete-then-write."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.SCRAPING_SUCCESSFUL)
        mock_summary.return_value = (make_summary(4), datetime.now(dt_timezone.utc))
        mock_docs.return_value = make_documents(4)

        ingest_scraped_collection(collection.id, claim=False)
        ingest_scraped_collection(collection.id, claim=False)

        assert DumpUrl.objects.filter(collection=collection).count() == 4

    @patch("sde_collections.tasks.fetch_documents", side_effect=Exception("S3 read died"))
    @patch("sde_collections.tasks.results_ready")
    def test_ingest_failure_after_claim_sets_scraping_failed(self, mock_ready, mock_docs):
        """Never leave a claimed collection stuck in SCRAPING_SUCCESSFUL with no DumpUrls."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(3)

        result = ingest_scraped_collection(collection.id)  # must not raise

        assert result is None
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.SCRAPING_FAILED

    @patch("sde_collections.tasks.send_detailed_import_notification")
    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.results_ready")
    def test_rescrape_path_ends_ready_for_recuration(self, mock_ready, mock_docs, mock_slack):
        """reindexing NEEDED -> ingest claims to FINISHED -> migrate task promotes to
        REINDEXING_READY_FOR_CURATION (the migrate task's existing transition)."""
        collection = CollectionFactory(
            workflow_status=WorkflowStatusChoices.PROD_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV,
        )
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(2)
        mock_docs.return_value = make_documents(2)

        with patch(
            "sde_collections.models.collection.migrate_dump_to_delta_and_handle_status_transistions.delay"
        ) as mock_delay:
            ingest_scraped_collection(collection.id)

        collection.refresh_from_db()
        assert collection.reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
        assert collection.workflow_status == WorkflowStatusChoices.PROD_PERFECT  # untouched
        mock_delay.assert_called_once_with(collection.id)

        # Now run the migration task for real (the .delay was mocked above).
        migrate_dump_to_delta_and_handle_status_transistions(collection.id)

        collection.refresh_from_db()
        assert collection.reindexing_status == ReindexingStatusChoices.REINDEXING_READY_FOR_CURATION
        mock_slack.assert_called_once()

    @patch("sde_collections.tasks.send_detailed_import_notification")
    @patch("sde_collections.tasks.fetch_documents")
    @patch("sde_collections.tasks.results_ready")
    def test_end_to_end_reaches_ready_for_curation_with_inference_off(
        self, mock_ready, mock_docs, mock_slack
    ):
        """P2+P4 integration: ingest -> SCRAPING_SUCCESSFUL -> migrate -> READY_FOR_CURATION,
        with the ingest summary posted to Slack."""
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(3)
        mock_docs.return_value = make_documents(3)

        with patch(
            "sde_collections.models.collection.migrate_dump_to_delta_and_handle_status_transistions.delay"
        ) as mock_delay:
            ingest_scraped_collection(collection.id)
        mock_delay.assert_called_once_with(collection.id)

        migrate_dump_to_delta_and_handle_status_transistions(collection.id)

        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.READY_FOR_CURATION
        assert collection.delta_urls.count() == 3
        mock_slack.assert_called_once()
        assert mock_slack.call_args.kwargs["dump_count"] == 3
        assert mock_slack.call_args.kwargs["delta_count"] == 3


@pytest.mark.django_db
class TestPollScrapeJobs:
    @patch("sde_collections.tasks.ingest_scraped_collection.delay")
    @patch("sde_collections.tasks.results_ready")
    def test_fresh_results_enqueue_ingest(self, mock_ready, mock_ingest):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(3)

        poll_scrape_jobs()

        mock_ingest.assert_called_once_with(collection.id)

    @patch("sde_collections.tasks.ingest_scraped_collection.delay")
    @patch("sde_collections.tasks.results_ready", return_value=None)
    def test_missing_summary_leaves_collection_waiting(self, mock_ready, mock_ingest):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")

        poll_scrape_jobs()

        mock_ingest.assert_not_called()
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.READY_FOR_ENGINEERING

    @patch("sde_collections.tasks.ingest_scraped_collection.delay")
    @patch("sde_collections.tasks.results_ready", return_value=None)
    def test_stall_timeout_marks_scraping_failed(self, mock_ready, mock_ingest):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)
        dispatch = ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        backdate_dispatch(dispatch, hours=25)  # default timeout is 24h

        poll_scrape_jobs()

        mock_ingest.assert_not_called()
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.SCRAPING_FAILED

    @patch("sde_collections.tasks.ingest_scraped_collection.delay")
    @patch("sde_collections.tasks.results_ready")
    def test_undispatched_collection_is_skipped(self, mock_ready, mock_ingest):
        CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)

        poll_scrape_jobs()

        mock_ready.assert_not_called()
        mock_ingest.assert_not_called()

    @patch("sde_collections.tasks.ingest_scraped_collection.delay")
    @patch("sde_collections.tasks.results_ready")
    def test_rescrape_collections_are_polled(self, mock_ready, mock_ingest):
        collection = CollectionFactory(
            workflow_status=WorkflowStatusChoices.PROD_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV,
        )
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")
        mock_ready.return_value = make_summary(2)

        poll_scrape_jobs()

        mock_ingest.assert_called_once_with(collection.id)


def _s3_stub(get_object=None):
    """Patchable session whose s3 client's get_object returns (or raises) the given value."""
    s3 = MagicMock()
    if isinstance(get_object, BaseException):
        s3.get_object.side_effect = get_object
    else:
        s3.get_object.return_value = get_object
    session = MagicMock()
    session.client.return_value = s3
    return session, s3


def _client_error(code):
    return ClientError({"Error": {"Code": code}}, "GetObject")


def _s3_object(payload, last_modified=None):
    return {
        "Body": io.BytesIO(json.dumps(payload).encode("utf-8")),
        "LastModified": last_modified or datetime(2026, 8, 13, 12, 0, 0, tzinfo=dt_timezone.utc),
    }


class TestS3ResultFetchers:
    """The S3 boundary itself: the ingest/poll tests all mock fetch_summary/fetch_documents,
    so the real key layout, bucket wiring and missing-key handling must be proven here.
    The keys are the crawler's contract (sde_crawler/job.py::s3_keys_for_collection)."""

    @pytest.fixture(autouse=True)
    def crawler_bucket(self):
        # override_settings can't decorate a plain (non-SimpleTestCase) class
        with override_settings(SDE_S3_BUCKET="crawler-bucket-test"):
            yield

    def test_fetch_summary_reads_crawler_summary_key_and_returns_last_modified(self):
        summary = make_summary(7)
        modified = datetime(2026, 8, 14, 9, 30, 0, tzinfo=dt_timezone.utc)
        session, s3 = _s3_stub(_s3_object(summary, modified))

        with patch("sde_collections.scraping.s3_results.get_boto3_session", return_value=session):
            result = fetch_summary("astro_data")

        assert result == (summary, modified)
        s3.get_object.assert_called_once_with(
            Bucket="crawler-bucket-test", Key="failure_logs/astro_data_failures_summary.json"
        )

    @pytest.mark.parametrize("code", ["NoSuchKey", "404"])
    def test_fetch_summary_missing_key_means_run_not_finished(self, code):
        session, _ = _s3_stub(_client_error(code))

        with patch("sde_collections.scraping.s3_results.get_boto3_session", return_value=session):
            assert fetch_summary("astro_data") is None

    def test_fetch_summary_propagates_real_s3_errors(self):
        """AccessDenied etc. must surface, not read as 'still crawling' forever."""
        session, _ = _s3_stub(_client_error("AccessDenied"))

        with patch("sde_collections.scraping.s3_results.get_boto3_session", return_value=session):
            with pytest.raises(ClientError):
                fetch_summary("astro_data")

    def test_fetch_documents_reads_scraped_collections_key(self):
        documents = make_documents(2)
        session, s3 = _s3_stub(_s3_object(documents))

        with patch("sde_collections.scraping.s3_results.get_boto3_session", return_value=session):
            result = fetch_documents("astro_data")

        assert result == documents
        s3.get_object.assert_called_once_with(
            Bucket="crawler-bucket-test", Key="scraped_collections/astro_data.json"
        )


class TestResultsFreshness:
    """Stale-results regression guard: a summary older than the dispatch is treated as absent."""

    @patch("sde_collections.scraping.s3_results.fetch_summary")
    def test_stale_summary_is_treated_as_absent(self, mock_fetch):
        dispatched_at = datetime(2026, 8, 13, 12, 0, 0, tzinfo=dt_timezone.utc)
        mock_fetch.return_value = (make_summary(5), dispatched_at - timedelta(hours=2))

        assert results_ready("some_collection", dispatched_at) is None

    @patch("sde_collections.scraping.s3_results.fetch_summary")
    def test_fresh_summary_is_returned(self, mock_fetch):
        dispatched_at = datetime(2026, 8, 13, 12, 0, 0, tzinfo=dt_timezone.utc)
        summary = make_summary(5)
        mock_fetch.return_value = (summary, dispatched_at + timedelta(minutes=10))

        assert results_ready("some_collection", dispatched_at) == summary

    @patch("sde_collections.scraping.s3_results.fetch_summary", return_value=None)
    def test_missing_summary_returns_none(self, mock_fetch):
        assert results_ready("some_collection", timezone.now()) is None

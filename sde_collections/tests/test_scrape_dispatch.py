# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_dispatch.py

from unittest.mock import patch

import pytest

from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.scraper_config import ScrapeDispatch, ScraperConfigOverride
from sde_collections.scraping.job_builder import build_job_json
from sde_collections.tasks import dispatch_scrape_job
from sde_collections.tests.factories import CollectionFactory


@pytest.mark.django_db
class TestBuildJobJson:
    def test_no_overrides_emits_exactly_seed_and_collection_id(self):
        collection = CollectionFactory()

        job = build_job_json(collection)

        assert job == {"seed": collection.url, "collection_id": collection.config_folder}

    def test_null_override_fields_are_omitted(self):
        """crawl4ai's merge_job() skips None — COSMOS must emit only non-null overrides."""
        collection = CollectionFactory()
        ScraperConfigOverride.objects.create(collection=collection, max_pages=5000, delay=None)

        job = build_job_json(collection)

        assert job["max_pages"] == 5000
        assert "delay" not in job
        assert "depth_limit" not in job
        assert "obey_robots" not in job

    def test_false_boolean_override_is_emitted(self):
        """False is a real override (e.g. include_subdomains=False), only None is skipped."""
        collection = CollectionFactory()
        ScraperConfigOverride.objects.create(collection=collection, include_subdomains=False)

        job = build_job_json(collection)

        assert job["include_subdomains"] is False

    def test_max_pages_above_crawler_cap_raises(self):
        collection = CollectionFactory()
        ScraperConfigOverride.objects.create(collection=collection, max_pages=200_000)

        with pytest.raises(ValueError, match="100000"):
            build_job_json(collection)


@pytest.mark.django_db
class TestStatusTriggersDispatch:
    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_ready_for_engineering_dispatches_scrape_job(self, mock_delay):
        collection = CollectionFactory()
        collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        collection.save()

        mock_delay.assert_called_once_with(collection.id)

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_reindexing_needed_dispatches_scrape_job(self, mock_delay):
        collection = CollectionFactory()
        collection.reindexing_status = ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
        collection.save()

        mock_delay.assert_called_once_with(collection.id)

    @patch("sde_collections.models.collection.Collection.create_scraper_config")
    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_ready_for_engineering_no_longer_touches_sinequa_configs(self, mock_delay, mock_scraper_config):
        collection = CollectionFactory()
        collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        collection.save()

        mock_scraper_config.assert_not_called()


@pytest.mark.django_db
class TestDispatchScrapeJobTask:
    @patch("sde_collections.tasks.send_job_to_crawler", return_value="cmd-abc123")
    def test_successful_dispatch_records_scrape_dispatch(self, mock_send):
        collection = CollectionFactory()

        result = dispatch_scrape_job(collection.id)

        assert result == "cmd-abc123"
        dispatch = ScrapeDispatch.objects.get(collection=collection)
        assert dispatch.ssm_command_id == "cmd-abc123"
        assert dispatch.dispatched_at is not None

    @patch("sde_collections.tasks.send_job_to_crawler", side_effect=Exception("SSM unreachable"))
    def test_ssm_failure_sets_scraping_failed_and_does_not_raise(self, mock_send):
        collection = CollectionFactory(workflow_status=WorkflowStatusChoices.READY_FOR_ENGINEERING)

        result = dispatch_scrape_job(collection.id)  # must not raise

        assert result is None
        collection.refresh_from_db()
        assert collection.workflow_status == WorkflowStatusChoices.SCRAPING_FAILED
        assert not ScrapeDispatch.objects.filter(collection=collection).exists()

    @patch("sde_collections.tasks.send_job_to_crawler", return_value="cmd-2")
    def test_redispatch_keeps_prior_dispatch_rows(self, mock_send):
        """Rows are never deleted — the poller takes the latest per collection."""
        collection = CollectionFactory()
        ScrapeDispatch.objects.create(collection=collection, ssm_command_id="cmd-1")

        dispatch_scrape_job(collection.id)

        ids = list(
            ScrapeDispatch.objects.filter(collection=collection).values_list("ssm_command_id", flat=True)
        )
        assert set(ids) == {"cmd-1", "cmd-2"}
        # Meta.ordering is -dispatched_at: first row is the latest dispatch
        assert ScrapeDispatch.objects.filter(collection=collection).first().ssm_command_id == "cmd-2"

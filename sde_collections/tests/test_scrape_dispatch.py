# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_scrape_dispatch.py

import json
import shlex
from unittest.mock import MagicMock, patch

import pytest
from django.test import override_settings

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.scraper_config import ScrapeDispatch, ScraperConfigOverride
from sde_collections.scraping.job_builder import build_job_json
from sde_collections.scraping.ssm_dispatch import send_job_to_crawler
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

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_ready_for_engineering_no_longer_touches_sinequa_configs(self, mock_delay):
        """P6 deleted the Sinequa config methods outright — the trigger can only dispatch."""
        from sde_collections.models.collection import Collection

        collection = CollectionFactory()
        collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        collection.save()

        mock_delay.assert_called_once_with(collection.id)
        assert not hasattr(Collection, "create_scraper_config")
        assert not hasattr(Collection, "create_scraper_job")


@pytest.mark.django_db
class TestSendJobToCrawler:
    """The SSM boundary itself: every caller-side test mocks send_job_to_crawler, so the
    script construction (quoting, atomic write, inbox path) must be proven here."""

    @pytest.fixture(autouse=True)
    def crawler_settings(self):
        # override_settings can't decorate a plain (non-SimpleTestCase) class
        with override_settings(
            CRAWLER_INSTANCE_ID="i-0test", CRAWLER_INBOX_PATH="/opt/sde-crawler/jobs/incoming"
        ):
            yield

    def _dispatch(self, collection):
        ssm = MagicMock()
        ssm.send_command.return_value = {"Command": {"CommandId": "cmd-xyz"}}
        session = MagicMock()
        session.client.return_value = ssm
        with patch("sde_collections.scraping.ssm_dispatch.get_boto3_session", return_value=session):
            command_id = send_job_to_crawler(collection)
        return command_id, ssm.send_command.call_args.kwargs

    def test_command_targets_crawler_instance_and_returns_command_id(self):
        collection = CollectionFactory()

        command_id, kwargs = self._dispatch(collection)

        assert command_id == "cmd-xyz"
        assert kwargs["InstanceIds"] == ["i-0test"]
        assert kwargs["DocumentName"] == "AWS-RunShellScript"

    def test_script_delivers_exact_job_json_via_atomic_rename(self):
        """Recover the payload by shell-splitting the script: what the shell would hand to
        printf must round-trip back to build_job_json's output, and the write must land on
        a .tmp path that is mv'd into the inbox last (the watcher must never see a partial
        file)."""
        collection = CollectionFactory()

        _, kwargs = self._dispatch(collection)

        lines = kwargs["Parameters"]["commands"][0].splitlines()
        dest = f"/opt/sde-crawler/jobs/incoming/{collection.config_folder}.json"

        printf_tokens = shlex.split(lines[0])
        assert printf_tokens[0] == "printf"
        assert json.loads(printf_tokens[2]) == build_job_json(collection)
        assert printf_tokens[-1] == dest + ".tmp"

        assert shlex.split(lines[1]) == ["chown", "ec2-user:ec2-user", dest + ".tmp"]
        assert shlex.split(lines[2]) == ["mv", "-f", dest + ".tmp", dest]

    def test_hostile_seed_url_survives_shell_quoting(self):
        """Seed URLs contain quotes/spaces/ampersands that would break an unquoted heredoc."""
        collection = CollectionFactory()
        Collection.objects.filter(id=collection.id).update(
            url="https://example.nasa.gov/search?q='solar wind'&page=1"
        )
        collection.refresh_from_db()

        _, kwargs = self._dispatch(collection)

        printf_tokens = shlex.split(kwargs["Parameters"]["commands"][0].splitlines()[0])
        payload = json.loads(printf_tokens[2])
        assert payload["seed"] == "https://example.nasa.gov/search?q='solar wind'&page=1"

    def test_comment_is_truncated_to_ssm_limit(self):
        collection = CollectionFactory()
        Collection.objects.filter(id=collection.id).update(config_folder="x" * 120)
        collection.refresh_from_db()

        _, kwargs = self._dispatch(collection)

        assert len(kwargs["Comment"]) <= 100
        assert kwargs["Comment"].startswith("COSMOS scrape dispatch:")


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

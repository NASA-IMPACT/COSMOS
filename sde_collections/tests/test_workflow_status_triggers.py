# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_workflow_status_triggers.py

from unittest.mock import patch

import pytest
from django.test import TestCase

from sde_collections.models.collection import Collection, WorkflowHistory
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.tests.factories import CollectionFactory


class TestWorkflowStatusTransitions(TestCase):
    """P5 trigger table: the dispatcher (handle_workflow_status_change) drives only the
    crawl4ai/indexing pipeline — every Sinequa branch is gone."""

    def setUp(self):
        self.collection = CollectionFactory()

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_ready_for_engineering_triggers_scrape_dispatch(self, mock_dispatch):
        """When status changes to READY_FOR_ENGINEERING, it should dispatch a scrape job (P3:
        replaces the Sinequa create_scraper_config/create_scraper_job trigger)."""
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        mock_dispatch.assert_called_once_with(self.collection.id)

    def _save_and_assert_no_triggers(self, **status_updates):
        """Set the given status field(s), save, and assert none of the surviving
        pipeline triggers fire. (The Sinequa methods can't be patched — they no
        longer exist; test_no_sinequa_methods_remain proves that directly.)"""
        with (
            patch("sde_collections.tasks.dispatch_scrape_job.delay") as mock_dispatch,
            patch("sde_collections.tasks.index_collection_to_test.delay") as mock_test,
            patch("sde_collections.tasks.index_collection_to_prod.delay") as mock_prod,
            patch("sde_collections.models.collection.Collection.promote_to_curated") as mock_promote,
        ):
            for field, value in status_updates.items():
                setattr(self.collection, field, value)
            self.collection.save()

        mock_dispatch.assert_not_called()
        mock_test.assert_not_called()
        mock_prod.assert_not_called()
        mock_promote.assert_not_called()

    def test_indexing_finished_triggers_nothing(self):
        """INDEXING_FINISHED_ON_DEV is a Sinequa-era status: its full-text-fetch trigger is
        gone (the P4 ingest replaces the fetch entirely)."""
        self._save_and_assert_no_triggers(workflow_status=WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV)

    def test_ready_for_curation_triggers_nothing(self):
        """The Sinequa indexer-config branch on READY_FOR_CURATION is gone."""
        self._save_and_assert_no_triggers(workflow_status=WorkflowStatusChoices.READY_FOR_CURATION)

    def test_no_sinequa_methods_remain(self):
        """P6: every Sinequa method is gone from Collection, and fetch_full_text from tasks."""
        from sde_collections import tasks

        for method in [
            "add_to_public_query",
            "create_scraper_config",
            "create_indexer_config",
            "create_scraper_job",
            "create_indexer_job",
            "update_config_xml",
            "import_metadata_from_sinequa_config",
            "sinequa_configuration",
            "server_url_prod",
            "server_url_secret_prod",
            "_write_to_github",
        ]:
            assert not hasattr(Collection, method), f"Collection.{method} should be deleted"
        for task in ["fetch_full_text", "import_candidate_urls_from_api", "push_to_github_task"]:
            assert not hasattr(tasks, task), f"tasks.{task} should be deleted"

    @patch("sde_collections.tasks.index_collection_to_test.delay")
    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_curated_promotes_and_enqueues_test_indexing(self, mock_promote, mock_index_test):
        """CURATED promotes DeltaUrls to CuratedUrls AND hands off to test indexing."""
        self.collection.workflow_status = WorkflowStatusChoices.CURATED
        self.collection.save()

        mock_promote.assert_called_once()
        mock_index_test.assert_called_once_with(self.collection.id)

    @patch("sde_collections.tasks.index_collection_to_prod.delay")
    def test_quality_check_statuses_enqueue_prod_indexing(self, mock_index_prod):
        """QC_PERFECT / QC_MINOR hand off to prod indexing (add_to_public_query is deleted)."""
        for status in [WorkflowStatusChoices.QUALITY_CHECK_PERFECT, WorkflowStatusChoices.QUALITY_CHECK_MINOR]:
            collection = CollectionFactory()
            collection.workflow_status = status
            collection.save()

            mock_index_prod.assert_called_with(collection.id)
        assert mock_index_prod.call_count == 2

    @patch("sde_collections.tasks.index_collection_to_test.delay")
    def test_reentrancy_guard_prevents_recursion(self, mock_index_test):
        """A save() performed inside a trigger must not re-fire the dispatcher."""

        def promote_and_save_again():
            # Simulates a trigger mutating and saving the same instance.
            self.collection.save()

        with patch(
            "sde_collections.models.collection.Collection.promote_to_curated",
            side_effect=promote_and_save_again,
        ) as mock_promote:
            self.collection.workflow_status = WorkflowStatusChoices.CURATED
            self.collection.save()

        mock_promote.assert_called_once()
        mock_index_test.assert_called_once()


class TestSlackNotificationOnTransition(TestCase):
    """P5: the Slack send moved out of Collection.save() into the post_save receiver."""

    def setUp(self):
        self.collection = CollectionFactory(workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS)

    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    @patch("sde_collections.models.collection.send_slack_message")
    def test_mapped_transition_sends_message_once(self, mock_send, mock_dispatch):
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        mock_send.assert_called_once()
        assert self.collection.name in mock_send.call_args.args[0] or "<" in mock_send.call_args.args[0]

    @patch("sde_collections.models.collection.send_slack_message")
    def test_unmapped_transition_sends_nothing(self, mock_send):
        self.collection.workflow_status = WorkflowStatusChoices.MERGE_PENDING
        self.collection.save()

        mock_send.assert_not_called()

    @patch("sde_collections.models.collection.send_slack_message", side_effect=Exception("slack down"))
    @patch("sde_collections.tasks.dispatch_scrape_job.delay")
    def test_slack_failure_does_not_break_the_save(self, mock_dispatch, mock_send):
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()  # must not raise

        self.collection.refresh_from_db()
        assert self.collection.workflow_status == WorkflowStatusChoices.READY_FOR_ENGINEERING


class TestReindexingStatusTransitions(TestCase):
    def setUp(self):
        self.collection = CollectionFactory(
            workflow_status=WorkflowStatusChoices.PROD_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NOT_NEEDED,
        )

    def test_reindexing_finished_triggers_nothing(self):
        """REINDEXING_FINISHED_ON_DEV must trigger nothing: the P4 ingest sets this status
        itself — a trigger here would double-fire."""
        with (
            patch("sde_collections.tasks.dispatch_scrape_job.delay") as mock_dispatch,
            patch("sde_collections.models.collection.Collection.promote_to_curated") as mock_promote,
        ):
            self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
            self.collection.save()

        mock_dispatch.assert_not_called()
        mock_promote.assert_not_called()

    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_reindexing_curated_triggers_promotion(self, mock_promote):
        """When reindexing status changes to CURATED, it should promote DeltaUrls"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_CURATED
        self.collection.save()

        mock_promote.assert_called_once()


NEW_PIPELINE_STATUSES = [
    WorkflowStatusChoices.SCRAPING_SUCCESSFUL,
    WorkflowStatusChoices.TEST_INDEXING,
    WorkflowStatusChoices.SCRAPING_FAILED,
    WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
    WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    WorkflowStatusChoices.PRODUCTION_INDEXING,
]

VALID_BUTTON_COLORS = {
    "btn-light",
    "btn-danger",
    "btn-warning",
    "btn-info",
    "btn-success",
    "btn-primary",
    "btn-secondary",
}


@pytest.mark.parametrize("status", list(WorkflowStatusChoices))
def test_collection_button_color_resolves_for_every_status(status):
    """Regression guard: an unmapped status used to raise KeyError and break the
    collection list and detail pages. Every enum member must resolve a colour."""
    collection = Collection(workflow_status=status)
    assert collection.workflow_status_button_color in VALID_BUTTON_COLORS


@pytest.mark.parametrize("status", list(WorkflowStatusChoices))
def test_workflow_history_button_color_resolves_for_every_status(status):
    history = WorkflowHistory(workflow_status=status)
    assert history.workflow_status_button_color in VALID_BUTTON_COLORS


def test_unmapped_status_falls_back_to_default_color():
    assert Collection(workflow_status=999).workflow_status_button_color == "btn-light"
    assert WorkflowHistory(workflow_status=999).workflow_status_button_color == "btn-light"


@pytest.mark.parametrize(
    "status",
    [
        WorkflowStatusChoices.SCRAPING_FAILED,
        WorkflowStatusChoices.INDEXING_FAILED_ON_TEST,
        WorkflowStatusChoices.INDEXING_FAILED_ON_PROD,
    ],
)
def test_failure_statuses_do_not_render_neutral(status):
    assert Collection(workflow_status=status).workflow_status_button_color == "btn-danger"
    assert WorkflowHistory(workflow_status=status).workflow_status_button_color == "btn-danger"


@pytest.mark.django_db
@pytest.mark.parametrize("status", NEW_PIPELINE_STATUSES)
def test_setting_new_status_writes_workflow_history(status):
    collection = CollectionFactory()
    collection.workflow_status = status
    collection.save()
    assert WorkflowHistory.objects.filter(collection=collection, workflow_status=status).exists()

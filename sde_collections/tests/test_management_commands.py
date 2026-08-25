# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_management_commands.py

from io import StringIO
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from sde_collections.tests.factories import CollectionFactory


@pytest.mark.django_db
class TestDispatchScrapeCommand:
    def test_unknown_collection_is_a_command_error(self):
        with pytest.raises(CommandError, match="No collection"):
            call_command("dispatch_scrape", collection="does_not_exist")

    @patch("sde_collections.management.commands.dispatch_scrape.dispatch_scrape_job", return_value="cmd-1")
    def test_runs_the_task_synchronously_and_reports_command_id(self, mock_task):
        collection = CollectionFactory()
        out = StringIO()

        call_command("dispatch_scrape", collection=collection.config_folder, stdout=out)

        mock_task.assert_called_once_with(collection.id)  # called directly, not .delay
        assert "cmd-1" in out.getvalue()

    @patch("sde_collections.management.commands.dispatch_scrape.dispatch_scrape_job", return_value=None)
    def test_dispatch_failure_is_a_command_error(self, mock_task):
        collection = CollectionFactory()

        with pytest.raises(CommandError, match="Dispatch failed"):
            call_command("dispatch_scrape", collection=collection.config_folder)


@pytest.mark.django_db
class TestIngestScrapeResultsCommand:
    def test_unknown_collection_is_a_command_error(self):
        with pytest.raises(CommandError, match="No collection"):
            call_command("ingest_scrape_results", collection="does_not_exist")

    @patch(
        "sde_collections.management.commands.ingest_scrape_results.ingest_scraped_collection",
        return_value="Ingested 3 documents",
    )
    def test_manual_ingest_skips_the_claim(self, mock_task):
        """The command's contract: explicit operator intent bypasses the status CAS."""
        collection = CollectionFactory()
        out = StringIO()

        call_command("ingest_scrape_results", collection=collection.config_folder, stdout=out)

        mock_task.assert_called_once_with(collection.id, claim=False)
        assert "Ingested 3 documents" in out.getvalue()

    @patch(
        "sde_collections.management.commands.ingest_scrape_results.ingest_scraped_collection",
        return_value=None,
    )
    def test_ingest_failure_is_a_command_error(self, mock_task):
        collection = CollectionFactory()

        with pytest.raises(CommandError, match="Ingest failed"):
            call_command("ingest_scrape_results", collection=collection.config_folder)

# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_workflow_status_triggers.py
from unittest.mock import Mock, patch

import pytest
from django.db import transaction
from django.test import TestCase, TransactionTestCase

from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from sde_collections.models.delta_url import DeltaUrl, DumpUrl
from sde_collections.tasks import fetch_and_replace_full_text
from sde_collections.tests.factories import CollectionFactory, DumpUrlFactory


class TestWorkflowStatusTransitions(TestCase):
    def setUp(self):
        self.collection = CollectionFactory()

    @patch("sde_collections.models.collection.Collection.create_scraper_config")
    @patch("sde_collections.models.collection.Collection.create_indexer_config")
    def test_ready_for_engineering_triggers_config_creation(self, mock_indexer, mock_scraper):
        """When status changes to READY_FOR_ENGINEERING, it should create configs"""
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        mock_scraper.assert_called_once_with(overwrite=False)
        mock_indexer.assert_called_once_with(overwrite=False)

    @patch("sde_collections.tasks.fetch_and_replace_full_text.delay")
    def test_indexing_finished_triggers_full_text_fetch(self, mock_fetch):
        """When status changes to INDEXING_FINISHED_ON_DEV, it should trigger full text fetch"""
        self.collection.workflow_status = WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV
        self.collection.save()

        mock_fetch.assert_called_once_with(self.collection.id, "lrm_dev")

    @patch("sde_collections.models.collection.Collection.create_plugin_config")
    def test_ready_for_curation_triggers_plugin_config(self, mock_plugin):
        """When status changes to READY_FOR_CURATION, it should create plugin config"""
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        self.collection.save()

        mock_plugin.assert_called_once_with(overwrite=True)

    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_curated_triggers_promotion(self, mock_promote):
        """When status changes to CURATED, it should promote DeltaUrls to CuratedUrls"""
        self.collection.workflow_status = WorkflowStatusChoices.CURATED
        self.collection.save()

        mock_promote.assert_called_once()

    @patch("sde_collections.models.collection.Collection.add_to_public_query")
    def test_quality_check_perfect_triggers_public_query(self, mock_add):
        """When status changes to QUALITY_CHECK_PERFECT, it should add to public query"""
        self.collection.workflow_status = WorkflowStatusChoices.QUALITY_CHECK_PERFECT
        self.collection.save()

        mock_add.assert_called_once()


class TestReindexingStatusTransitions(TestCase):
    def setUp(self):
        # Mock the GitHubHandler to return valid XML content
        self.mock_github_handler = patch("sde_collections.models.collection.GitHubHandler").start()

        self.mock_github_handler.return_value._get_file_contents.return_value.decoded_content = (
            b'<?xml version="1.0" encoding="UTF-8"?>\n'
            b"<Sinequa>\n"
            b"    <KeepHashFragmentInUrl>false</KeepHashFragmentInUrl>\n"
            b"    <CollectionSelection>Sample Collection</CollectionSelection>\n"
            b"</Sinequa>"
        )

        self.addCleanup(patch.stopall)

        # Create the collection with the mock applied
        self.collection = CollectionFactory(
            workflow_status=WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NOT_NEEDED,
        )

    @patch("sde_collections.tasks.fetch_and_replace_full_text.delay")
    def test_reindexing_finished_triggers_full_text_fetch(self, mock_fetch):
        """When reindexing status changes to FINISHED, it should trigger full text fetch"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV
        self.collection.save()

        mock_fetch.assert_called_once_with(self.collection.id, "lrm_dev")

    @patch("sde_collections.models.collection.Collection.promote_to_curated")
    def test_reindexing_curated_triggers_promotion(self, mock_promote):
        """When reindexing status changes to CURATED, it should promote DeltaUrls"""
        self.collection.reindexing_status = ReindexingStatusChoices.REINDEXING_CURATED
        self.collection.save()

        mock_promote.assert_called_once()


class TestFullTextImport(TestCase):
    def setUp(self):
        self.collection = CollectionFactory()
        self.existing_dump = DumpUrlFactory(collection=self.collection)
        self.api_response = [
            {"url": "http://example.com/1", "title": "Title 1", "full_text": "Content 1"},
            {"url": "http://example.com/2", "title": "Title 2", "full_text": "Content 2"},
        ]

    @patch("sde_collections.tasks.Api")
    @patch("sde_collections.models.collection.GitHubHandler")
    def test_full_text_import_workflow(self, MockGitHub, MockApi):
        """Test the full process of importing full text data"""
        # Setup mock GitHub handler with proper XML content
        mock_github = Mock()
        mock_github.check_file_exists.return_value = True
        mock_file_contents = Mock()
        # Include all the fields that convert_template_to_plugin_indexer checks for
        mock_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <Sinequa>
            <KeepHashFragmentInUrl>false</KeepHashFragmentInUrl>
            <CorrectDomainCookies>false</CorrectDomainCookies>
            <IgnoreSessionCookies>false</IgnoreSessionCookies>
            <DownloadImages>false</DownloadImages>
            <DownloadMedia>false</DownloadMedia>
            <DownloadCss>false</DownloadCss>
            <DownloadFtp>true</DownloadFtp>
            <DownloadFile>true</DownloadFile>
            <IndexJs>false</IndexJs>
            <FollowJs>true</FollowJs>
            <CrawlFlash>true</CrawlFlash>
            <NormalizeUrls>true</NormalizeUrls>
            <NormalizeSecureSchemesWhenTestingVisited>True</NormalizeSecureSchemesWhenTestingVisited>
            <UrlAccess>
                <AllowXPathCookies>false</AllowXPathCookies>
                <UseBrowserForWebRequests>true</UseBrowserForWebRequests>
                <UseHttpClientForWebRequests>false</UseHttpClientForWebRequests>
            </UrlAccess>
            <RetryCount></RetryCount>
            <RetryPause></RetryPause>
            <AddBaseHref></AddBaseHref>
            <AddMetaContentType></AddMetaContentType>
        </Sinequa>"""
        mock_file_contents.decoded_content = mock_xml.encode("utf-8")
        mock_github._get_file_contents.return_value = mock_file_contents
        MockGitHub.return_value = mock_github

        # Setup mock API
        mock_api = Mock()
        mock_api.get_full_texts.return_value = [self.api_response]
        MockApi.return_value = mock_api

        # Setup initial workflow state
        self.collection.workflow_status = WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV
        self.collection.save()

        # Run the import
        fetch_and_replace_full_text(self.collection.id, "lrm_dev")

        # Verify old DumpUrls were cleared
        assert not DumpUrl.objects.filter(id=self.existing_dump.id).exists()

        # Verify new Delta urls were created
        new_deltas = DeltaUrl.objects.filter(collection=self.collection)
        assert new_deltas.count() == 2
        assert {dump.url for dump in new_deltas} == {"http://example.com/1", "http://example.com/2"}

        # Verify status updates
        self.collection.refresh_from_db()
        assert self.collection.workflow_status == WorkflowStatusChoices.READY_FOR_CURATION


class TestErrorHandling(TransactionTestCase):
    def setUp(self):
        self.collection = CollectionFactory(workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS)

    @patch("sde_collections.models.collection.Collection.create_scraper_config")
    @patch("sde_collections.models.collection.Collection.create_indexer_config")
    def test_config_creation_failure_handling(self, mock_indexer, mock_scraper):
        """Test handling of config creation failures"""
        mock_scraper.side_effect = Exception("Config creation failed")

        initial_status = self.collection.workflow_status

        with pytest.raises(Exception):
            with transaction.atomic():
                self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
                self.collection.save()

        # Verify status wasn't changed on error
        self.collection.refresh_from_db()
        assert self.collection.workflow_status == initial_status

    @patch("sde_collections.tasks.Api")
    def test_full_text_fetch_failure_handling(self, MockApi):
        """Test handling of full text fetch failures"""
        mock_api = Mock()
        mock_api.get_full_texts.side_effect = Exception("API error")
        MockApi.return_value = mock_api

        initial_status = self.collection.workflow_status

        with pytest.raises(Exception):
            fetch_and_replace_full_text(self.collection.id, "lrm_dev")

        # Verify status wasn't changed on error
        self.collection.refresh_from_db()
        assert self.collection.workflow_status == initial_status

from django.test import TestCase
from unittest.mock import patch, call, MagicMock
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices

'''
Workflow status change → Opens template → Applies XML transformation → Writes to GitHub.

- When the `workflow_status` changes, it triggers the relevant config creation method.
- The method reads an template and processes it using `XmlEditor`.
- `XmlEditor` modifies the template by injecting collection-specific values and transformations.
- The generated XML is passed to `_write_to_github()`, which commits it directly to GitHub.

Note: This test verifies that the correct methods are triggered and XML content is passed to GitHub.
The actual XML structure and correctness are tested separately in `test_db_xml.py`.
'''

class TestConfigCreation(TestCase):
    def setUp(self):
        self.collection = Collection.objects.create(
            name="Test Collection",
            division="1",
            workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS
        )

    @patch('sde_collections.utils.github_helper.GitHubHandler')  # Mock GitHubHandler
    @patch('sde_collections.models.collection.Collection._write_to_github')
    @patch('sde_collections.models.collection.XmlEditor')
    def test_ready_for_engineering_triggers_config_and_job_creation(self, MockXmlEditor, mock_write_to_github, MockGitHubHandler):
        """
        When the collection's workflow status is updated to READY_FOR_ENGINEERING,
        it should trigger the creation of scraper configuration and job files.
        """
        # Mock GitHubHandler to avoid actual API calls
        mock_github_instance = MockGitHubHandler.return_value
        mock_github_instance.create_file.return_value = None
        mock_github_instance.create_or_update_file.return_value = None

        # Set up the XmlEditor mock for both config and job
        mock_editor_instance = MockXmlEditor.return_value
        mock_editor_instance.convert_template_to_scraper.return_value = '<scraper_config>config_data</scraper_config>'
        mock_editor_instance.convert_template_to_job.return_value = '<scraper_job>job_data</scraper_job>'

        # Simulate the status change to READY_FOR_ENGINEERING
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_ENGINEERING
        self.collection.save()

        # Verify that the XML for both config and job are generated and written to GitHub
        expected_calls = [
            call(self.collection._scraper_config_path, '<scraper_config>config_data</scraper_config>', False),
            call(self.collection._scraper_job_path, '<scraper_job>job_data</scraper_job>', False)
        ]
        mock_write_to_github.assert_has_calls(expected_calls, any_order=True)

    @patch('sde_collections.models.collection.GitHubHandler')  # Mock GitHubHandler in the correct module path
    @patch('sde_collections.models.collection.Collection._write_to_github')
    @patch('sde_collections.models.collection.XmlEditor')
    def test_ready_for_curation_triggers_indexer_config_and_job_creation(self, MockXmlEditor, mock_write_to_github, MockGitHubHandler):
        """
        When the collection's workflow status is updated to READY_FOR_CURATION,
        it should trigger indexer config and job creation methods.
        """
        # Mock GitHubHandler to avoid actual API calls
        mock_github_instance = MockGitHubHandler.return_value
        mock_github_instance.check_file_exists.return_value = True  # Assume scraper exists
        mock_github_instance._get_file_contents.return_value = MagicMock()
        mock_github_instance._get_file_contents.return_value.decoded_content = b"<scraper_config>Mock Data</scraper_config>"

        # Set up the XmlEditor mock for both config and job
        mock_editor_instance = MockXmlEditor.return_value
        mock_editor_instance.convert_template_to_indexer.return_value = '<indexer_config>config_data</indexer_config>'
        mock_editor_instance.convert_template_to_job.return_value = '<indexer_job>job_data</indexer_job>'

        # Simulate the status change to READY_FOR_CURATION
        self.collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        self.collection.save()

        # Verify that the XML for both indexer config and job are generated and written to GitHub
        expected_calls = [
            call(self.collection._indexer_config_path, '<indexer_config>config_data</indexer_config>', True),
            call(self.collection._indexer_job_path, '<indexer_job>job_data</indexer_job>', False)
        ]
        mock_write_to_github.assert_has_calls(expected_calls, any_order=True)

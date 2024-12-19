# docker-compose -f local.yml run --rm django pytest sde_collections/tests/api_tests.py
from unittest.mock import MagicMock, patch

import pytest
import requests
from django.utils import timezone

from sde_collections.models.collection import WorkflowStatusChoices
from sde_collections.sinequa_api import Api
from sde_collections.tests.factories import CollectionFactory, UserFactory


@pytest.mark.django_db
class TestApiClass:
    @pytest.fixture
    def collection(self):
        """Fixture to create a collection object for testing."""
        user = UserFactory()
        return CollectionFactory(
            curated_by=user,
            curation_started=timezone.now(),
            config_folder="example_config",
            workflow_status=WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
        )

    @pytest.fixture
    def api_instance(self):
        """Fixture to create an Api instance with mocked server configs."""
        with patch(
            "sde_collections.sinequa_api.server_configs",
            {
                "test_server": {
                    "app_name": "test_app",
                    "query_name": "test_query",
                    "base_url": "http://testserver.com/api",
                    "index": "test_index",
                }
            },
        ):
            return Api(server_name="test_server", user="test_user", password="test_pass", token="test_token")

    @patch("requests.post")
    def test_process_response_success(self, mock_post, api_instance):
        """Test that process_response handles successful responses."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_post.return_value = mock_response

        response = api_instance.process_response("http://example.com", payload={"test": "data"})
        assert response == {"key": "value"}

    @patch("requests.post")
    def test_process_response_failure(self, mock_post, api_instance):
        """Test that process_response raises an exception on failure."""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_post.return_value = mock_response
        mock_response.raise_for_status.side_effect = Exception("Internal Server Error")

        with pytest.raises(Exception, match="Internal Server Error"):
            api_instance.process_response("http://example.com", payload={"test": "data"})

    @patch("sde_collections.sinequa_api.Api.process_response")
    def test_query(self, mock_process_response, api_instance):
        """Test that query sends correct payload and processes response."""
        mock_process_response.return_value = {"result": "success"}
        response = api_instance.query(page=1, collection_config_folder="folder")
        assert response == {"result": "success"}

    def test_process_rows_to_records(self, api_instance):
        """Test processing row data into record dictionaries."""
        # Test valid input
        valid_rows = [["http://example.com/1", "Text 1", "Title 1"], ["http://example.com/2", "Text 2", "Title 2"]]
        expected_output = [
            {"url": "http://example.com/1", "full_text": "Text 1", "title": "Title 1"},
            {"url": "http://example.com/2", "full_text": "Text 2", "title": "Title 2"},
        ]
        assert api_instance._process_rows_to_records(valid_rows) == expected_output

        # Test invalid row length
        invalid_rows = [["http://example.com", "Text"]]  # Missing title
        with pytest.raises(ValueError, match="Invalid row format at index 0"):
            api_instance._process_rows_to_records(invalid_rows)

    @patch("sde_collections.sinequa_api.Api.process_response")
    def test_execute_sql_query(self, mock_process_response, api_instance):
        """Test SQL query execution."""
        mock_process_response.return_value = {"Rows": [], "TotalRowCount": 0}

        # Test successful query
        result = api_instance._execute_sql_query("SELECT * FROM test")
        assert result == {"Rows": [], "TotalRowCount": 0}

        # Test query with missing token
        api_instance._provided_token = None
        with pytest.raises(ValueError, match="Token is required"):
            api_instance._execute_sql_query("SELECT * FROM test")

    @patch("sde_collections.sinequa_api.Api._execute_sql_query")
    def test_get_full_texts_pagination(self, mock_execute_sql, api_instance):
        """Test that get_full_texts correctly handles pagination."""
        # Mock responses for two pages of results
        mock_execute_sql.side_effect = [
            {
                "Rows": [["http://example.com/1", "Text 1", "Title 1"], ["http://example.com/2", "Text 2", "Title 2"]],
                "TotalRowCount": 3,
            },
            {"Rows": [["http://example.com/3", "Text 3", "Title 3"]], "TotalRowCount": 3},
            {"Rows": [], "TotalRowCount": 3},
        ]

        # Collect all batches from the iterator
        batches = list(api_instance.get_full_texts("test_folder"))

        assert len(batches) == 2  # Should have two batches
        assert len(batches[0]) == 2  # First batch has 2 records
        assert len(batches[1]) == 1  # Second batch has 1 record

        # Verify content of first batch
        assert batches[0] == [
            {"url": "http://example.com/1", "full_text": "Text 1", "title": "Title 1"},
            {"url": "http://example.com/2", "full_text": "Text 2", "title": "Title 2"},
        ]

        # Verify content of second batch
        assert batches[1] == [{"url": "http://example.com/3", "full_text": "Text 3", "title": "Title 3"}]

    def test_get_full_texts_missing_index(self, api_instance):
        """Test that get_full_texts raises error when index is missing from config."""
        api_instance.config.pop("index", None)
        with pytest.raises(ValueError, match="Index not defined for server"):
            next(api_instance.get_full_texts("test_folder"))

    @pytest.mark.parametrize(
        "server_name,expect_auth",
        [
            ("xli", True),  # dev server should have auth
            ("production", False),  # prod server should not have auth
        ],
    )
    @patch("requests.post")
    def test_query_authentication(self, mock_post, server_name, expect_auth, api_instance):
        """Test authentication handling for different server types."""
        api_instance.server_name = server_name
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"result": "success"})

        response = api_instance.query(page=1, collection_config_folder="folder")
        assert response == {"result": "success"}

        called_url = mock_post.call_args[0][0]
        auth_present = "?Password=test_pass&User=test_user" in called_url
        assert auth_present == expect_auth

    @patch("requests.post")
    def test_query_dev_server_missing_credentials(self, mock_post, api_instance):
        """Test that dev servers raise error when credentials are missing."""
        api_instance.server_name = "xli"
        api_instance._provided_user = None
        api_instance._provided_password = None

        with pytest.raises(ValueError, match="Authentication error: Missing credentials for dev server"):
            api_instance.query(page=1)

    @patch("sde_collections.sinequa_api.Api._execute_sql_query")
    def test_get_full_texts_batch_size_reduction(self, mock_execute_sql, api_instance):
        """Test that batch size reduces appropriately on failure and continues processing."""
        # Mock first query to fail, then succeed with smaller batch
        mock_execute_sql.side_effect = [
            requests.RequestException("Query too large"),  # First attempt fails
            {
                "Rows": [["http://example.com/1", "Text 1", "Title 1"]],
                "TotalRowCount": 1,
            },  # Succeeds with smaller batch
        ]

        batches = list(api_instance.get_full_texts("test_folder", batch_size=100, min_batch_size=1))

        # Verify the batches were processed correctly after size reduction
        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0]["url"] == "http://example.com/1"

        # Verify the calls made - first with original size, then with reduced size
        assert mock_execute_sql.call_count == 2
        first_call = mock_execute_sql.call_args_list[0][0][0]
        second_call = mock_execute_sql.call_args_list[1][0][0]
        assert "COUNT 100" in first_call
        assert "COUNT 50" in second_call  # Should be halved from 100

    @patch("sde_collections.sinequa_api.Api._execute_sql_query")
    def test_get_full_texts_minimum_batch_size(self, mock_execute_sql, api_instance):
        """Test behavior when reaching minimum batch size."""
        mock_execute_sql.side_effect = requests.RequestException("Query failed")

        # Start with batch_size=4, min_batch_size=1
        # Should try: 4 -> 2 -> 1 -> raise error
        with pytest.raises(ValueError, match="Failed to process batch even at minimum size 1"):
            list(api_instance.get_full_texts("test_folder", batch_size=4, min_batch_size=1))

        # Should have tried 3 times before giving up
        assert mock_execute_sql.call_count == 3
        calls = mock_execute_sql.call_args_list
        assert "COUNT 4" in calls[0][0][0]  # First try with 4
        assert "COUNT 2" in calls[1][0][0]  # Second try with 2
        assert "COUNT 1" in calls[2][0][0]  # Final try with 1

    @patch("sde_collections.sinequa_api.Api._execute_sql_query")
    def test_get_full_texts_batch_size_progression(self, mock_execute_sql, api_instance):
        """Test multiple batch size reductions followed by successful query."""
        mock_execute_sql.side_effect = [
            requests.RequestException("First failure"),
            requests.RequestException("Second failure"),
            {"Rows": [["http://example.com/1", "Text 1", "Title 1"]], "TotalRowCount": 1},
        ]

        # Start with batch_size=100, should reduce to 25 before succeeding
        batches = list(api_instance.get_full_texts("test_folder", batch_size=100, min_batch_size=1))

        assert len(batches) == 1  # Should get one successful batch
        assert mock_execute_sql.call_count == 3

        calls = mock_execute_sql.call_args_list
        # Verify the progression of batch sizes
        assert "COUNT 100" in calls[0][0][0]  # First attempt
        assert "COUNT 50" in calls[1][0][0]  # After first failure
        assert "COUNT 25" in calls[2][0][0]  # After second failure

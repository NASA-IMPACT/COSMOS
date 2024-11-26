# docker-compose -f local.yml run --rm django pytest sde_collections/tests/api_tests.py
from unittest.mock import MagicMock, patch

import pytest
from django.utils import timezone

from sde_collections.models.collection import WorkflowStatusChoices
from sde_collections.models.delta_url import DumpUrl
from sde_collections.sinequa_api import Api
from sde_collections.tasks import fetch_and_replace_full_text
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

    @patch("sde_collections.sinequa_api.Api.process_response")
    def test_sql_query(self, mock_process_response, api_instance, collection):
        """Test SQL query execution and response processing."""
        mock_process_response.return_value = {
            "Rows": [{"url": "http://example.com", "full_text": "Text", "title": "Title"}],
            "TotalRowCount": 1,
        }
        response = api_instance.sql_query("SELECT * FROM test_index", collection)
        assert response == "All 1 records have been processed and updated."

    @patch("sde_collections.sinequa_api.Api.process_response")
    def test_get_full_texts(self, mock_process_response, api_instance, collection):
        """Test fetching full texts from the API."""
        mock_process_response.return_value = {
            "Rows": [{"url": "http://example.com", "text": "Example text", "title": "Example title"}]
        }
        response = api_instance.get_full_texts(
            collection_config_folder="folder", source="source", collection=collection
        )
        assert response == "All 0 records have been processed and updated."

    def test_process_and_update_data(self, api_instance, collection):
        """Test processing and updating data in the database."""
        batch_data = [{"url": "http://example.com", "full_text": "Example text", "title": "Example title"}]
        api_instance.process_and_update_data(batch_data, collection)
        dump_urls = DumpUrl.objects.filter(collection=collection)
        assert dump_urls.count() == 1
        assert dump_urls.first().url == "http://example.com"

    @patch("sde_collections.sinequa_api.Api.sql_query")
    @patch("sde_collections.models.collection.Collection.migrate_dump_to_delta")
    def test_fetch_and_replace_full_text(self, mock_migrate, mock_sql_query, collection):
        """Test the fetch_and_replace_full_text Celery task."""
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
            mock_sql_query.return_value = "All records processed"
            mock_migrate.return_value = None

            result = fetch_and_replace_full_text(collection.id, "test_server")
            assert result == "All records processed"
            mock_migrate.assert_called_once()

    @patch(
        "sde_collections.sinequa_api.server_configs",
        {
            "test_server": {
                "app_name": "test_app",
                "query_name": "test_query",
                "base_url": "http://testserver.com/api",
                "index": "test_index",
            }
        },
    )
    @pytest.mark.parametrize(
        "server_name, user, password, expected",
        [("test_server", "user1", "pass1", True), ("invalid_server", None, None, False)],
    )
    def test_api_init(self, server_name, user, password, expected):
        """Test API initialization with valid and invalid server names."""
        if expected:
            api = Api(server_name=server_name, user=user, password=password)
            assert api.server_name == server_name
        else:
            with pytest.raises(ValueError):
                Api(server_name=server_name)

    @patch("requests.post")
    def test_query_dev_server_authentication(self, mock_post, api_instance):
        """Test query on dev servers requiring authentication."""
        api_instance.server_name = "xli"
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"result": "success"})

        response = api_instance.query(page=1, collection_config_folder="folder")
        assert response == {"result": "success"}

        # Extract URL from call_args (positional arguments)
        called_url = mock_post.call_args[0][0]  # URL is the first positional argument
        assert "?Password=test_pass&User=test_user" in called_url

    @patch("sde_collections.sinequa_api.Api.process_response")
    def test_sql_query_pagination(self, mock_process_response, api_instance, collection):
        """Test SQL query with pagination."""
        mock_process_response.side_effect = [
            {"Rows": [{"url": "http://example.com/1", "full_text": "Text 1", "title": "Title 1"}], "TotalRowCount": 6},
            {"Rows": [{"url": "http://example.com/2", "full_text": "Text 2", "title": "Title 2"}], "TotalRowCount": 6},
            {"Rows": [], "TotalRowCount": 6},
        ]

        result = api_instance.sql_query("SELECT * FROM test_index", collection)
        assert result == "All 6 records have been processed and updated."

    def test_process_full_text_response(self, api_instance):
        """Test that _process_full_text_response correctly processes the data."""
        batch_data = {
            "Rows": [
                ["http://example.com", "Example text", "Example title"],
                ["http://example.net", "Another text", "Another title"],
            ]
        }
        expected_output = [
            {"url": "http://example.com", "full_text": "Example text", "title": "Example title"},
            {"url": "http://example.net", "full_text": "Another text", "title": "Another title"},
        ]
        result = api_instance._process_full_text_response(batch_data)
        assert result == expected_output

    def test_process_full_text_response_with_invalid_data(self, api_instance):
        """Test that _process_full_text_response raises an error with invalid data."""
        # Test for missing 'Rows' key
        invalid_data_no_rows = {}  # No 'Rows' key
        with pytest.raises(ValueError, match="Expected 'Rows' key with a list of data"):
            api_instance._process_full_text_response(invalid_data_no_rows)

        # Test for incorrect row length
        invalid_data_wrong_length = {"Rows": [["http://example.com", "Example text"]]}  # Missing 'title'
        with pytest.raises(ValueError, match="Each row must contain exactly three elements"):
            api_instance._process_full_text_response(invalid_data_wrong_length)

    @patch("sde_collections.sinequa_api.Api._get_token", return_value=None)
    def test_sql_query_missing_token(self, mock_get_token, api_instance, collection):
        """Test that sql_query raises an error when no token is provided."""
        with pytest.raises(ValueError, match="A token is required to use the SQL endpoint"):
            api_instance.sql_query("SELECT * FROM test_table", collection)

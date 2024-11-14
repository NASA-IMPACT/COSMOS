# docker-compose -f local.yml run --rm django pytest sde_collections/tests/api_tests.py
import unittest
from unittest.mock import Mock, patch
from requests import HTTPError
from ..sinequa_api import Api

class TestApi(unittest.TestCase):
    def setUp(self):
        # Set up an instance of the Api class with parameters for testing
        self.api = Api(server_name="test", user="test_user", password="test_password", token="test_token")

    @patch("requests.post")
    def test_process_response_success(self, mock_post):
        # This test checks the process_response method when the HTTP request is successful
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_post.return_value = mock_response

        response = self.api.process_response("http://example.com/api", payload={"test": "data"})
        self.assertEqual(response, {"key": "value"})
        mock_post.assert_called_once()

    @patch("requests.post")
    def test_process_response_failure(self, mock_post):
        # Create a mock response object with a 500 status code
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {"error": "Internal Server Error"}
        mock_post.return_value = mock_response

        def raise_for_status():
            if mock_response.status_code != 200:
                raise HTTPError(
                    f"{mock_response.status_code} Server Error: Internal Server Error for url: http://example.com/api"
                )

        mock_response.raise_for_status = raise_for_status

        # Attempt to process the response and check if it correctly handles the HTTP error
        with self.assertRaises(HTTPError):
            self.api.process_response("http://example.com/api", payload={"test": "data"})

    @patch("requests.post")
    def test_query(self, mock_post):
        """
        The test ensures that the query method constructs the correct URL and payload based on input parameters,
          and processes a successful API response to return the expected data
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"key": "value"}
        mock_post.return_value = mock_response

        response = self.api.query(page=1, collection_config_folder="sample_folder")
        self.assertEqual(response, {"key": "value"})

        expected_url = "https://sciencediscoveryengine.test.nasa.gov/api/v1/search.query"
        expected_payload = {
            "app": "nasa-sba-smd",
            "query": {
                "name": "query-smd-primary",
                "text": "",
                "page": 1,
                "pageSize": 1000,
                "advanced": {"collection": "/SDE/sample_folder/"},
            },
        }
        mock_post.assert_called_once_with(expected_url, headers={}, json=expected_payload, verify=False)

    @patch("requests.post")
    def test_sql_query(self, mock_post):
        # Mock response for the `sql_query` function with token-based authentication
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"Rows": [["http://example.com", "sample text", "sample title"]]}
        mock_post.return_value = mock_response

        sql = "SELECT url1, text, title FROM sde_index WHERE collection = '/SDE/sample_folder/'"
        response = self.api.sql_query(sql)
        self.assertEqual(response, {"Rows": [["http://example.com", "sample text", "sample title"]]})

    @patch("requests.post")
    def test_get_full_texts(self, mock_post):
        # Mock response for the `get_full_texts` method
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "Rows": [
                ["http://example.com/article1", "Here is the full text of the first article...", "Article One Title"],
                ["http://example.com/article2", "Here is the full text of the second article...", "Article Two Title"],
            ]
        }
        mock_post.return_value = mock_response

        result = self.api.get_full_texts(collection_config_folder="sample_folder")
        expected = [
            {
                "url": "http://example.com/article1",
                "full_text": "Here is the full text of the first article...",
                "title": "Article One Title",
            },
            {
                "url": "http://example.com/article2",
                "full_text": "Here is the full text of the second article...",
                "title": "Article Two Title",
            },
        ]
        self.assertEqual(result, expected)

    def test_missing_token_for_sql_query(self):
        # To test when token is missing for sql_query
        api = Api(server_name="test", token=None)
        with self.assertRaises(ValueError):
            api.sql_query("SELECT * FROM test_table")

    def test_process_full_text_response(self):
        # Test `_process_full_text_response` parsing functionality
        raw_response = {
            "Rows": [
                ["http://example.com/article1", "Full text for article 1", "Title 1"],
                ["http://example.com/article2", "Full text for article 2", "Title 2"],
            ]
        }
        processed_response = Api._process_full_text_response(raw_response)
        expected = [
            {"url": "http://example.com/article1", "full_text": "Full text for article 1", "title": "Title 1"},
            {"url": "http://example.com/article2", "full_text": "Full text for article 2", "title": "Title 2"},
        ]
        self.assertEqual(processed_response, expected)

if __name__ == "__main__":
    unittest.main()

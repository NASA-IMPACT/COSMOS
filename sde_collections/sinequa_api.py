import json
from collections.abc import Iterator
from typing import Any

import requests
import urllib3
from django.conf import settings

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

server_configs = {
    "dev": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-renaissance.nasa-impact.net",
    },
    "test": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
        "index": "sde_index",
    },
    "production": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
        "index": "sde_index",
    },
    "secret_test": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
        "index": "sde_index",
    },
    "secret_production": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
        "index": "sde_index",
    },
    "xli": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-xli.nasa-impact.net",
        "index": "sde_index",
    },
    "lrm_dev": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": "https://sde-lrm.nasa-impact.net",
        "index": "sde_init_check",
    },
    "lrm_qa": {
        "app_name": "sde-init-check",
        "query_name": "query-init-check",
        "base_url": "https://sde-qa.nasa-impact.net",
    },
}


class Api:
    def __init__(self, server_name: str = None, user: str = None, password: str = None, token: str = None) -> None:
        self.server_name = server_name
        if server_name not in server_configs:
            raise ValueError(f"Invalid server configuration: '{server_name}' is not a recognized server name")

        self.config = server_configs[server_name]
        self.app_name: str = self.config["app_name"]
        self.query_name: str = self.config["query_name"]
        self.base_url: str = self.config["base_url"]
        self.dev_servers = ["xli", "lrm_dev", "lrm_qa"]

        self._provided_user = user
        self._provided_password = password
        self._provided_token = token

    def _get_user(self) -> str | None:
        """Retrieve the user, using the provided value or defaulting to Django settings."""
        return self._provided_user or getattr(settings, f"{self.server_name}_USER".upper(), None)

    def _get_password(self) -> str | None:
        """Retrieve the password, using the provided value or defaulting to Django settings."""
        return self._provided_password or getattr(settings, f"{self.server_name}_PASSWORD".upper(), None)

    def _get_token(self) -> str | None:
        """Retrieve the token, using the provided value or defaulting to Django settings."""
        return self._provided_token or getattr(settings, f"{self.server_name}_TOKEN".upper(), None)

    def _get_source_name(self) -> str:
        """by default, the source is /SDE/. However for the various dev servers, the source is tends to be /scrapers/"""
        return "scrapers" if self.server_name in self.dev_servers else "SDE"

    def process_response(
        self,
        url: str,
        payload: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        raw_data: str | None = None,
    ) -> Any:
        """Sends a POST request and processes the response."""
        response = requests.post(
            url, headers=headers, json=payload if raw_data is None else None, data=raw_data, verify=False
        )
        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            response.raise_for_status()

    def query(self, page: int, collection_config_folder: str | None = None, source: str | None = None) -> Any:
        url = f"{self.base_url}/api/v1/search.query"
        if self.server_name in self.dev_servers:
            user = self._get_user()
            password = self._get_password()
            if not user or not password:
                raise ValueError(
                    f"Authentication error: Missing credentials for dev server '{self.server_name}'. "
                    f"Both username and password are required for servers: {', '.join(self.dev_servers)}"
                )
            authentication = f"?Password={password}&User={user}"
            url = f"{url}{authentication}"

        payload = {
            "app": self.app_name,
            "query": {
                "name": self.query_name,
                "text": "",
                "page": page,
                "pageSize": 1000,
                "advanced": {},
            },
        }

        if collection_config_folder:
            source = source if source else self._get_source_name()
            payload["query"]["advanced"]["collection"] = f"/{source}/{collection_config_folder}/"

        return self.process_response(url, payload)

    def _execute_sql_query(self, sql: str) -> dict:
        """
        Executes a SQL query against the Sinequa API.

        Args:
            sql (str): The SQL query to execute

        Returns:
            dict: The JSON response from the API containing 'Rows' and 'TotalRowCount'

        Raises:
            ValueError: If no token is available for authentication
        """
        token = self._get_token()
        if not token:
            raise ValueError("Authentication error: Token is required for SQL endpoint access")

        url = f"{self.base_url}/api/v1/engine.sql"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        raw_payload = json.dumps(
            {
                "method": "engine.sql",
                "sql": sql,
                "pretty": True,
            }
        )

        return self.process_response(url, headers=headers, raw_data=raw_payload)

    def _process_rows_to_records(self, rows: list) -> list[dict]:
        """
        Converts raw SQL row data into structured record dictionaries.

        Args:
            rows (list): List of rows, where each row is [url, full_text, title]

        Returns:
            list[dict]: List of processed records with url, full_text, and title keys

        Raises:
            ValueError: If any row doesn't contain exactly 3 elements
        """
        processed_records = []
        for idx, row in enumerate(rows):
            if len(row) != 3:
                raise ValueError(
                    f"Invalid row format at index {idx}: Expected exactly three elements (url, full_text, title). "
                    f"Received {len(row)} elements."
                )
            processed_records.append({"url": row[0], "full_text": row[1], "title": row[2]})
        return processed_records

    def get_full_texts(self, collection_config_folder: str, source: str = None) -> Iterator[dict]:
        """
        Retrieves and yields batches of text records from the SQL database for a given collection.
        Uses pagination to handle large datasets efficiently.

        Args:
            collection_config_folder (str): The collection folder to query (e.g., "EARTHDATA", "SMD")
            source (str, optional): The source to query. If None, defaults to "scrapers" for dev servers
                or "SDE" for other servers.

        Yields:
            list[dict]: Batches of records, where each record is a dictionary containing:
                {
                    "url": str,       # The URL of the document
                    "full_text": str, # The full text content of the document
                    "title": str      # The title of the document
                }

        Raises:
            ValueError: If the server's index is not defined in its configuration

        Example batch:
            [
                {
                    "url": "https://example.nasa.gov/doc1",
                    "full_text": "This is the content of doc1...",
                    "title": "Document 1 Title"
                },
                {
                    "url": "https://example.nasa.gov/doc2",
                    "full_text": "This is the content of doc2...",
                    "title": "Document 2 Title"
                }
            ]

        Note:
            - Results are paginated in batches of 5000 records
            - Each batch is processed into clean dictionaries before being yielded
            - The iterator will stop when either:
                1. No more rows are returned from the query
                2. The total count of records has been reached
        """

        if not source:
            source = self._get_source_name()

        if (index := self.config.get("index")) is None:
            raise ValueError(
                f"Configuration error: Index not defined for server '{self.server_name}'. "
                "Please update server configuration with the required index."
            )

        sql = f"SELECT url1, text, title FROM {index} WHERE collection = '/{source}/{collection_config_folder}/'"

        page = 0
        page_size = 5000
        total_processed = 0

        while True:
            paginated_sql = f"{sql} SKIP {total_processed} COUNT {page_size}"
            response = self._execute_sql_query(paginated_sql)

            rows = response.get("Rows", [])
            if not rows:  # Stop if we get an empty batch
                break

            yield self._process_rows_to_records(rows)

            total_processed += len(rows)
            total_count = response.get("TotalRowCount", 0)

            if total_processed >= total_count:  # Stop if we've processed all records
                break

            page += 1

    @staticmethod
    def _process_full_text_response(batch_data: dict):
        if "Rows" not in batch_data or not isinstance(batch_data["Rows"], list):
            raise ValueError(
                "Invalid response format: Expected 'Rows' key with list data in Sinequa server response. "
                f"Received: {type(batch_data.get('Rows', None))}"
            )

        processed_data = []
        for idx, row in enumerate(batch_data["Rows"]):
            if len(row) != 3:
                raise ValueError(
                    f"Invalid row format at index {idx}: Expected exactly three elements (url, full_text, title). "
                    f"Received {len(row)} elements."
                )
            url, full_text, title = row
            processed_data.append({"url": url, "full_text": full_text, "title": title})
        return processed_data

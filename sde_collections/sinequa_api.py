import json
from typing import Any

import requests
import urllib3
from django.conf import settings
from django.db import transaction

from .models.delta_url import DumpUrl

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

    def sql_query(self, sql: str, collection) -> Any:
        token = self._get_token()
        if not token:
            raise ValueError("Authentication error: Token is required for SQL endpoint access")

        page = 0
        page_size = 5000  # Number of records per page
        skip_records = 0

        while True:
            paginated_sql = f"{sql} SKIP {skip_records} COUNT {page_size}"
            url = f"{self.base_url}/api/v1/engine.sql"
            headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
            raw_payload = json.dumps(
                {
                    "method": "engine.sql",
                    "sql": paginated_sql,
                    "pretty": True,
                }
            )

            response = self.process_response(url, headers=headers, raw_data=raw_payload)
            batch_data = response.get("Rows", [])
            total_row_count = response.get("TotalRowCount", 0)
            processed_response = self._process_full_text_response(response)
            self.process_and_update_data(processed_response, collection)

            # Check if all rows have been fetched
            if len(batch_data) == 0 or (skip_records + page_size) >= total_row_count:
                break

            page += 1
            skip_records += page_size

        return f"All {total_row_count} records have been processed and updated."

    def process_and_update_data(self, batch_data, collection):
        for record in batch_data:
            try:
                with transaction.atomic():
                    url = record["url"]
                    scraped_text = record.get("full_text", "")
                    scraped_title = record.get("title", "")
                    DumpUrl.objects.update_or_create(
                        url=url,
                        defaults={
                            "scraped_text": scraped_text,
                            "scraped_title": scraped_title,
                            "collection": collection,
                        },
                    )
            except KeyError as e:
                print(f"Missing key in data: {str(e)}")
            except Exception as e:
                print(f"Error processing record: {str(e)}")

    def get_full_texts(self, collection_config_folder: str, source: str = None, collection=None) -> Any:
        """
        Retrieves the full texts, URLs, and titles for a specified collection.

        Returns:
            dict: A JSON response containing the results of the SQL query,
                where each item has 'url', 'text', and 'title'.

        Example:
            Calling get_full_texts("example_collection") might return:
                [
                    {
                        'url': 'http://example.com/article1',
                        'text': 'Here is the full text of the first article...',
                        'title': 'Article One Title'
                    },
                    {
                        'url': 'http://example.com/article2',
                        'text': 'Here is the full text of the second article...',
                        'title': 'Article Two Title'
                    }
                ]
        """

        if not source:
            source = self._get_source_name()

        if (index := self.config.get("index")) is None:
            raise ValueError(
                f"Configuration error: Index not defined for server '{self.server_name}'. "
                "Please update server configuration with the required index."
            )

        sql = f"SELECT url1, text, title FROM {index} WHERE collection = '/{source}/{collection_config_folder}/'"
        return self.sql_query(sql, collection)

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

import json
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
            raise ValueError(f"Server name '{server_name}' is not in server_configs")

        self.config = server_configs[server_name]
        self.app_name: str = self.config["app_name"]
        self.query_name: str = self.config["query_name"]
        self.base_url: str = self.config["base_url"]
        self.dev_servers = ["xli", "lrm_dev", "lrm_qa"]

        # Store provided values only
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

    def process_response(self, url: str, payload: dict[str, Any]) -> Any:
        response = requests.post(url, headers={}, json=payload, verify=False)

        if response.status_code == requests.codes.ok:
            return response.json()
        else:
            response.raise_for_status()

    def query(self, page: int, collection_config_folder: str = None, source: str = None) -> Any:
        url = f"{self.base_url}/api/v1/search.query"
        if self.server_name in self.dev_servers:
            user = self._get_user()
            password = self._get_password()

            if not user or not password:
                raise ValueError(
                    "User and password are required for the query endpoint on the following servers: {self.dev_servers}"
                )
            authentication = f"?Password={password}&User={user}"
            url = f"{url}{authentication}"
        else:
            url = f"{self.base_url}/api/v1/search.query"

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

    def sql_query(self, sql: str) -> Any:
        """Executes an SQL query on the configured server using token-based authentication."""
        token = self._get_token()
        if not token:
            raise ValueError("A token is required to use the SQL endpoint")
        url = f"{self.base_url}/api/v1/engine.sql"
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
        payload = json.dumps(
            {
                "method": "engine.sql",
                "sql": sql,
                "pretty": True,
                "log": False,
                "output": "json",
                "resolveIndexList": "false",
                "engines": "default",
            }
        )

        try:
            response = requests.post(url, headers=headers, data=payload, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Api request to SQL endpoint failed: {str(e)}")

    def get_full_texts(self, collection_config_folder: str, source: str = None) -> Any:
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
            raise ValueError("Index not defined for this server")

        sql = f"SELECT url1, text, title FROM {index} WHERE collection = '/{source}/{collection_config_folder}/'"
        full_text_response = self.sql_query(sql)
        return self._process_full_text_response(full_text_response)

    @staticmethod
    def _process_full_text_response(full_text_response: str):
        return [
            {"url": url, "full_text": full_text, "title": title} for url, full_text, title in full_text_response["Rows"]
        ]

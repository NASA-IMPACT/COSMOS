from typing import Any

import requests

server_configs: dict[str, dict[str, str]] = {
    "test_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
    },
    "production_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
    },
}


class Api:
    def __init__(self, server_name: str = "test", token: str = None) -> None:
        self.app_name: str = server_configs[server_name]["app_name"]
        self.query_name: str = server_configs[server_name]["query_name"]
        self.base_url: str = server_configs[server_name]["base_url"]
        self.token: str = token  # you don't need a token for the query endpoint

    def _process_response(self, response) -> dict[str, Any]:
        if response.status_code == 200:
            meaningful_response = response.json()
        else:
            meaningful_response = {"response_text": response.text}

        return meaningful_response

    def query(self, term: str):
        url = f"{self.base_url}/api/v1/search.query"
        payload = {
            "app": self.app_name,
            "query": {
                "name": self.query_name,
                "action": "search",
                "text": term,
                "pageSize": 1000,
                "tab": "all",
            },
            "pretty": "true",
        }
        response = requests.post(url, json=payload, verify=False)

        return self._process_response(response)

    def sql(
        self, source: str = "SMD", collection: str = "", fetch_all: bool = False
    ) -> dict[str, Any]:
        if not self.token:
            raise ValueError("you must have a token to use the SQL endpoint")

        url = f"{self.base_url}/api/v1/engine.sql"

        collection_name = f"/{source}/{collection}/"
        sql_command_all = (
            "select url1,title,collection from @@ScienceMissionDirectorate"
        )
        if fetch_all:
            sql_command = sql_command_all
        else:
            sql_command = f"{sql_command_all} where collection='{collection_name}'"

        payload = {
            "sql": sql_command,
            "maxRows": 10000000,  # ten million
            "pretty": "true",
        }
        response = requests.post(
            url,
            headers={"Authorization": f"Bearer {self.token}"},
            json=payload,
            verify=False,
        )

        return self._process_response(response)

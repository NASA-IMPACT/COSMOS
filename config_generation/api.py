from typing import Any

import requests

from config import tokens

server_configs: dict[str, dict[str, str]] = {
    "ren_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-renaissance.nasa-impact.net",
    },
    "test_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://10.51.14.135",
    },
}


class Api:
    def __init__(self, server_name: str) -> None:
        self.headers: dict[str, str] = {"Authorization": f"Bearer {tokens[server_name]}"}
        self.app_name: str = server_configs[server_name]["app_name"]
        self.query_name: str = server_configs[server_name]["query_name"]
        self.base_url: str = server_configs[server_name]["base_url"]

    def process_response(self, url: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = requests.post(url, headers=self.headers, json=payload, verify=False)

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

        return self.process_response(url, payload)

    def sql(self, source: str, collection: str = "", fetch_all: bool = False) -> dict[str, Any]:
        url = f"{self.base_url}/api/v1/engine.sql"

        collection_name = f"/{source}/{collection}/"
        sql_command_all = "select url1,title,collection from @@ScienceMissionDirectorate"
        if fetch_all:
            sql_command = sql_command_all
        else:
            sql_command = f"{sql_command_all} where collection='{collection_name}'"

        payload = {
            "sql": sql_command,
            "maxRows": 10000000,  # ten million
            "pretty": "true",
        }
        response = self.process_response(url, payload)

        return response

    def run_indexer(self, source_name: str, collection_name: str) -> dict[str, Any]:
        """Starts indexing on the given collection. Equivalent to pressing the play button in the
        interface. This function will return the response from the sinequa server and then the
        server will run the collection on it's own without restraining the python execution.

        Args:
            source_name (str): this is the name of the source in sinequa, for example, Scraping or SMD
            collection_name (str): for example astro_home_page
        """
        url = f"{self.base_url}/api/v1/operation.collectionStart"

        payload = {
            "collection": f"/{source_name}/{collection_name}/",
        }

        return self.process_response(url, payload)

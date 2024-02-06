from typing import Any

import requests
import urllib3

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
    },
    "production": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
    },
    "secret_test": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.test.nasa.gov",
    },
    "secret_production": {
        "app_name": "nasa-sba-sde",
        "query_name": "query-sde-primary",
        "base_url": "https://sciencediscoveryengine.nasa.gov",
    },
    "lis_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "http://sde-xli.nasa-impact.net",
    },
}


class Api:
    def __init__(self, server_name: str) -> None:
        self.app_name: str = server_configs[server_name]["app_name"]
        self.query_name: str = server_configs[server_name]["query_name"]
        self.base_url: str = server_configs[server_name]["base_url"]

    def process_response(self, url: str, payload: dict[str, Any]) -> Any:
        response = requests.post(url, headers={}, json=payload, verify=False)

        if response.status_code == requests.status_codes.codes.ok:
            meaningful_response = response.json()
        else:
            raise Exception(response.text)

        return meaningful_response

    def query(self, page: int, collection_config_folder: str = "") -> Any:
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
            payload["query"]["advanced"][
                "collection"
            ] = f"/SDE/{collection_config_folder}/"

        response = self.process_response(url, payload)

        return response

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
    "lrm_dev_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sde-lrm.nasa-impact.net",
    },
    "lrm_qa_server": {
        "app_name": "nasa-sba-smd",
        "query_name": "query-smd-primary",
        "base_url": "https://sde-qa.nasa-impact.net",
    },
}


class Api:
    def __init__(self, server_name: str) -> None:
        self.server_name = server_name
        self.app_name: str = server_configs[server_name]["app_name"]
        self.query_name: str = server_configs[server_name]["query_name"]
        self.base_url: str = server_configs[server_name]["base_url"]
        self.xli_user = settings.XLI_USER
        self.xli_password = settings.XLI_PASSWORD
        self.lrm_user = settings.LRM_USER
        self.lrm_password = settings.LRM_PASSWORD
        self.lrm_qa_user = settings.LRM_QA_USER
        self.lrm_qa_password = settings.LRM_QA_PASSWORD

    def process_response(self, url: str, payload: dict[str, Any]) -> Any:
        response = requests.post(url, headers={}, json=payload, verify=False)

        if response.status_code == requests.status_codes.codes.ok:
            meaningful_response = response.json()
        else:
            raise Exception(response.text)

        return meaningful_response

    def query(self, page: int, collection_config_folder: str = "") -> Any:
        if self.server_name == "lis_server":
            url = f"{self.base_url}/api/v1/search.query?Password={self.xli_password}&User={self.xli_user}"
        elif self.server_name == "lrm_dev_server":
            url = f"{self.base_url}/api/v1/search.query?Password={self.lrm_password}&User={self.lrm_user}"
        elif self.server_name == "lrm_qa_server":
            url = f"{self.base_url}/api/v1/search.query?Password={self.lrm_qa_password}&User={self.lrm_qa_user}"
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
            if self.server_name == "lis_server":
                payload["query"]["advanced"]["collection"] = f"/scrapers/{collection_config_folder}/"
            else:
                payload["query"]["advanced"]["collection"] = f"/SDE/{collection_config_folder}/"

        response = self.process_response(url, payload)

        return response

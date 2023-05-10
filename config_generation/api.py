from typing import Any

import requests

from config import token


class Api:
    def __init__(self) -> None:
        self.headers: dict[str, str] = {"Authorization": f"Bearer {token}"}
        self.app_name: str = "nasa-sba-smd"
        self.query_name: str = "query-smd-primary"
        self.base_url: str = "http://sde-renaissance.nasa-impact.net"

    def process_response(self, url: str, payload: dict[str, Any]) -> None:
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            print("Data retrieved successfully!")
            meaningful_response = response.json()
        else:
            print(f"Request failed with status code: {response.status_code}")
            meaningful_response = response.text

        return meaningful_response

    def query(self, term: str) -> None:
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

        response = self.process_response(url, payload)

        return response

    def run_indexer(self, source_name: str, collection_name: str) -> None:
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

        response = self.process_response(url, payload)

        return response


if __name__ == "__main__":
    api = Api()
    from sources_to_scrape import remaining_sources

    for source in remaining_sources[5:10]:
        print(source["source_name"])
        api.run_indexer(source["source_name"])

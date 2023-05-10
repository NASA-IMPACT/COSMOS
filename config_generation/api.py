import requests

from config import token


class Api:
    def __init__(self):
        self.headers = {"Authorization": f"Bearer {token}"}
        self.app_name = "nasa-sba-smd"
        self.query_name = "query-smd-primary"
        self.base_url = "http://sde-renaissance.nasa-impact.net"

    def process_response(self, url, payload):
        response = requests.post(url, headers=self.headers, json=payload)

        if response.status_code == 200:
            print("Data retrieved successfully!")
            print(response.json())
        else:
            print(f"Request failed with status code: {response.status_code}")
            print(response.text)

    def query(self, term):
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

        self.process_response(url, payload)

    def run_indexer(self, collection_name="quotes"):
        url = f"{self.base_url}/api/v1/operation.collectionStart"

        payload = {
            "collection": f"/Scraping/{collection_name}/",
        }

        self.process_response(url, payload)


if __name__ == "__main__":
    api = Api()
    from sources_to_scrape import remaining_sources

    for source in remaining_sources[5:10]:
        print(source["source_name"])
        api.run_indexer(source["source_name"])

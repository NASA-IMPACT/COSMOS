import json

import requests
from api import Api
from generate_collection_list import turned_on_remaining_webcrawlers

api = Api("test_server")

for collection in turned_on_remaining_webcrawlers:
    print(collection)
    BASE_URL = "https://sde-indexing-helper.nasa-impact.net"
    POST_URL = f"{BASE_URL}/api/candidate-urls/{collection}/bulk-create/"

    response = api.sql("SMD", collection)

    # TODO: save response to a csv with f'{collection}.xml' as the name
    candidate_urls = response["Rows"]
    bulk_data = [
        {
            "url": candidate_url["url"],
            "scraped_title": candidate_url["title"],
        }
        for candidate_url in candidate_urls
    ]

    headers = {"Content-Type": "application/json"}
    response = requests.post(POST_URL, data=json.dumps(bulk_data), headers=headers)
    print(response.text)
    break

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
    print(len(candidate_urls))
    bulk_data = [
        {
            "url": candidate_url[0],
            "scraped_title": candidate_url[1],
        }
        for candidate_url in candidate_urls
    ]

    headers = {"Content-Type": "application/json"}
    response = requests.post(POST_URL, data=json.dumps(bulk_data), headers=headers)
    print(response.status_code)
    print("\n")



import json

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection

urls = json.load(open("solar_urls.json"))

collection = Collection.objects.get(name="Solar System Exploration")

for url in urls:
    candidate_url = CandidateURL.objects.create(
        url=url["url"],
        collection=Collection.objects.get(id=1),
        hash="1",
        scraped_title=url["title"],
        generated_title=url["generated_title"],
        visited=False,
        document_type=0,
        inferenced_by="",
        is_pdf=False,
        present_on_test=False,
        present_on_prod=False,
    )
    candidate_url.save()

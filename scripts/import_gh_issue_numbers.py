# run this in manage.py shell
import json

from sde_collections.models import Collection

myjson = json.load(open("sde_collections/fixtures/issue_numbers.json"))

for pk, github_issue_number in myjson.items():
    collection = Collection.objects.get(pk=pk)
    collection.github_issue_number = github_issue_number
    collection.save()

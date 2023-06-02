import json

from sde_collections.models import Collection

# run this in manage.py shell


myjson = json.load(open("jupyter_notebooks/myjson.json"))

for item in myjson:
    collection = Collection.objects.get(name=item["guess_title"])
    collection.github_issue_number = item["url"].split("/")[-1]
    collection.save()

# dump data

Collection.objects.values_list("id", "github_issue_number")
dict(Collection.objects.values_list("id", "github_issue_number"))
issue_number_dict = dict(Collection.objects.values_list("id", "github_issue_number"))
json.dump(
    issue_number_dict,
    open("sde_collections/fixtures/issue_numbers.json", "w"),
    indent=4,
)

# import on server

myjson = json.load(open("sde_collections/fixtures/issue_numbers.json"))

for pk, github_issue_number in myjson.items():
    collection = Collection.objects.get(pk=pk)
    collection.github_issue_number = github_issue_number
    collection.save()

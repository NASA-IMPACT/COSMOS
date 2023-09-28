"""
Sometimes it is necessary to programatically push many collections at once to github.
This code will search for collections matching a certain criteria (curated, pr created),
and push their changes to Github
"""

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import CurationStatusChoices
from sde_collections.utils.github_helper import GitHubHandler

finished_statuses = [
    CurationStatusChoices.CURATED,
    CurationStatusChoices.GITHUB_PR_CREATED,
]

collections = Collection.objects.filter(curation_status__in=finished_statuses)

gh = GitHubHandler(collections)
gh.push_to_github()

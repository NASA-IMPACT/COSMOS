import json

from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import Divisions, SourceChoices
from sde_collections.utils.github_helper import GitHubHandler


class Command(BaseCommand):
    help = (
        "Sync all collections with GitHub. Takes comma-separated config_folder list as argument."
        "If no argument is provided, all collections will be synced"
    )

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="*", type=str, default=[])

    # @staticmethod
    # def _get_names(collections):
    #     return list(collections.values_list("name", flat=True))

    def handle(self, *args, **options):
        gh = GitHubHandler(collections=Collection.objects.none())
        collections = gh.get_collections_from_github()

        with open("github_collections.json", "w") as f:
            json.dump(collections, f)

        for collection in collections:
            Collection.objects.create(
                config_folder=collection["config_folder"],
                name=collection["name"],
                url=collection["url"],
                division=Divisions.lookup_by_text(collection["division"]),
                document_type=collection["document_type"],
                source=SourceChoices.BOTH,
                connector=collection["connector"],
            )

        self.stdout.write(self.style.SUCCESS("Successfully synced"))

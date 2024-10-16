from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.utils.github_helper import GitHubHandler


class Command(BaseCommand):
    help = "Push config to github. Takes comma-separated config_folder list as argument."

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="*", type=str, default=[])

    @staticmethod
    def _get_names(collections):
        return list(collections.values_list("name", flat=True))

    def handle(self, *args, **options):
        selected_collections = Collection.objects.filter(config_folders=options["config_folders"])
        curated_collections = selected_collections.filter(workflow_status=WorkflowStatusChoices.CURATED)
        uncurated_collections = selected_collections.exclude(workflow_status=WorkflowStatusChoices.CURATED)

        gh = GitHubHandler(curated_collections)
        gh.push_to_github()

        self.stdout.write(self.style.SUCCESS("Successfully pushed: %s" % self._get_names(curated_collections)))

        if uncurated_collections:
            self.stdout.write(
                self.style.ERROR(
                    "The following collections could not be pushed because the workflow status was not Curated %s"
                    % self._get_names(uncurated_collections)
                )
            )

from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection
from sde_collections.utils.github_helper import GitHubHandler


class Command(BaseCommand):
    help = (
        "Push config to github. Takes comma-separated config_folder list as argument."
    )

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="*", type=str, default=[])

    def handle(self, *args, **options):
        config_folders = options["config_folders"]

        # curation status 5 is Curated
        collections = Collection.objects.filter(
            config_folder__in=config_folders
        ).filter(curation_status=5)

        cant_push = Collection.objects.filter(config_folder__in=config_folders).exclude(
            curation_status=5
        )
        cant_push = list(cant_push.values_list("name", flat=True))

        gh = GitHubHandler(collections)
        gh.push_to_github()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully pushed: %s"
                % list(collections.values_list("name", flat=True))
            )
        )

        if cant_push:
            self.stdout.write(
                self.style.ERROR(
                    "Can't push since status is not Curated (choice_id:5) %s"
                    % cant_push
                )
            )

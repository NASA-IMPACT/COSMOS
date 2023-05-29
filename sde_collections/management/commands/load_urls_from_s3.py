import json
from urllib.parse import urlparse

from django.core.management.base import BaseCommand

from sde_collections.tasks import import_candidate_urls_task


class Command(BaseCommand):
    help = "Load scraped URLs into the database"

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="*", type=str, default=[])

    def parse_jsonl(self, items):
        return [urlparse(json.loads(item)["url"]).path.split("/")[1:] for item in items]

    def handle(self, *args, **options):
        config_folders = options["config_folders"]
        import_candidate_urls_task(config_folder_names=config_folders)

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded data from "%s"' % config_folders)
        )

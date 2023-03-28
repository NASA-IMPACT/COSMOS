import json
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sde_collections.models import CandidateURL, Collection


class Command(BaseCommand):
    help = "Load scraped URLs into the database"

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="+", type=str)

    def handle(self, *args, **options):
        SCRAPED_URLS_DIR = f"{settings.BASE_DIR}/scraper/scraped_urls"
        for config_folder in options["config_folders"]:
            try:
                collection = Collection.objects.get(config_folder=config_folder)
            except Collection.DoesNotExist:
                raise CommandError(
                    'Collection with config folder "%s" does not exist' % config_folder
                )

            try:
                with open(f"{SCRAPED_URLS_DIR}/{config_folder}/urls.jsonl") as f:
                    items = [json.loads(line) for line in f.readlines()]
                    for item in items:
                        CandidateURL.objects.create(
                            collection=collection,
                            url=item["url"],
                            title=item["title"] or "",
                            depth=0,
                            path=urlparse(item["url"]).path,
                        )
            except FileNotFoundError:
                raise CommandError('No scraped URLs found for "%s"' % config_folder)

            self.stdout.write(
                self.style.SUCCESS('Successfully loaded data from "%s"' % config_folder)
            )

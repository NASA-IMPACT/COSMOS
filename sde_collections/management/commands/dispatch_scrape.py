from django.core.management.base import BaseCommand, CommandError

from sde_collections.models.collection import Collection
from sde_collections.tasks import dispatch_scrape_job


class Command(BaseCommand):
    help = "Manually (re-)dispatch a scrape job for a collection to the crawl4ai crawler via SSM."

    def add_arguments(self, parser):
        parser.add_argument("--collection", required=True, help="config_folder of the collection")

    def handle(self, *args, **options):
        config_folder = options["collection"]
        try:
            collection = Collection.objects.get(config_folder=config_folder)
        except Collection.DoesNotExist:
            raise CommandError(f"No collection with config_folder={config_folder!r}")

        # Run synchronously so the operator sees the outcome immediately.
        command_id = dispatch_scrape_job(collection.id)
        if command_id is None:
            raise CommandError(
                f"Dispatch failed for {config_folder} — see task output above; "
                f"collection is now marked Scraping Failed"
            )
        self.stdout.write(self.style.SUCCESS(f"Dispatched {config_folder}: SSM command {command_id}"))

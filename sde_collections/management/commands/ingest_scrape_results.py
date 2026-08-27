from django.core.management.base import BaseCommand, CommandError

from sde_collections.models.collection import Collection
from sde_collections.tasks import ingest_scraped_collection


class Command(BaseCommand):
    help = (
        "Manually ingest completed crawl results from S3 for a collection. Skips the "
        "status compare-and-swap (explicit operator intent) and ignores result freshness, "
        "but still deletes existing DumpUrls first, so re-runs are idempotent."
    )

    def add_arguments(self, parser):
        parser.add_argument("--collection", required=True, help="config_folder of the collection")

    def handle(self, *args, **options):
        config_folder = options["collection"]
        try:
            collection = Collection.objects.get(config_folder=config_folder)
        except Collection.DoesNotExist:
            raise CommandError(f"No collection with config_folder={config_folder!r}")

        # Run synchronously so the operator sees the outcome immediately.
        result = ingest_scraped_collection(collection.id, claim=False)
        if result is None:
            raise CommandError(f"Ingest failed for {config_folder} — see task output above")
        self.stdout.write(self.style.SUCCESS(str(result)))

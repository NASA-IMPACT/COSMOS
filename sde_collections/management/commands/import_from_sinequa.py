from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection


class Command(BaseCommand):
    help = "Load scraped URLs into the database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options) -> None:
        for collection in Collection.objects.all():
            if collection.import_metadata_from_sinequa_config():
                message = f"Successfully imported metadata from {collection.config_folder}"
                self.stdout.write(self.style.SUCCESS(message))
            else:
                message = f"Failed to import metadata from {collection.name}"
                self.stdout.write(self.style.ERROR(message))

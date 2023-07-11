from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection


class Command(BaseCommand):
    help = "Export config for collections"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def handle(self, *args, **options) -> None:
        collections = [
            "GISS Datasets and Derived Materials",
            "GISS Publication List",
            "NASA Global Climate Change",
            "Goddard Institute for Space Studies",
            "Earth Observer Publications",
            "Our Changing Planet: The View from Space Images",
            "NASA Sea Level Change",
            "NASA Carbon Monitoring System",
            "Algorithm Theoretical Basis Documents",
        ]

        for collection_name in collections:
            collection = Collection.objects.get(name=collection_name)
            collection.export_config()
            message = f"Successfully exported config for {collection.config_folder}"
            self.stdout.write(self.style.SUCCESS(message))

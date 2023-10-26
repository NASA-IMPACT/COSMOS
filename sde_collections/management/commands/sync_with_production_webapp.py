from django.core.management.base import BaseCommand

from sde_collections.tasks import sync_with_production_webapp


class Command(BaseCommand):
    help = "Load collections from the production webapp"

    def handle(self, *args, **options):
        sync_with_production_webapp()

        self.stdout.write(
            self.style.SUCCESS(
                "Successfully loaded collections from the webapp production."
            )
        )

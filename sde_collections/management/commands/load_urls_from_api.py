from django.core.management.base import BaseCommand

from sde_collections.tasks import import_candidate_urls_from_api


class Command(BaseCommand):
    help = "Load scraped URLs into the database"

    def handle(self, *args, **options):
        import_candidate_urls_from_api()

        self.stdout.write(self.style.SUCCESS("Successfully loaded urls from the test server"))

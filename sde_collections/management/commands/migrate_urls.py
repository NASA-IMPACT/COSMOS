from django.core.management.base import BaseCommand

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.models.curated_url import CuratedUrl
from sde_collections.models.delta_url import DeltaUrl


class Command(BaseCommand):
    help = "Migrate CandidateURLs to CuratedUrl or DeltaUrl based on collection workflow status"

    def handle(self, *args, **kwargs):
        # Migrate CandidateURLs for collections with CURATED or higher workflow status to CuratedUrl
        collections_for_curated = Collection.objects.filter(workflow_status__gte=WorkflowStatusChoices.CURATED)
        self.stdout.write(
            f"Migrating URLs for {collections_for_curated.count()} collections with CURATED or higher status..."
        )

        for collection in collections_for_curated:
            candidate_urls = CandidateURL.objects.filter(collection=collection)
            for candidate_url in candidate_urls:
                CuratedUrl.objects.create(
                    collection=candidate_url.collection,
                    url=candidate_url.url,
                    scraped_title=candidate_url.scraped_title,
                    generated_title=candidate_url.generated_title,
                    visited=candidate_url.visited,
                    document_type=candidate_url.document_type,
                    division=candidate_url.division,
                )
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to CuratedUrl."
            )

        # Migrate CandidateURLs for collections with a status lower than CURATED to DeltaUrl
        collections_for_delta = Collection.objects.filter(workflow_status__lt=WorkflowStatusChoices.CURATED)
        self.stdout.write(
            f"Migrating URLs for {collections_for_delta.count()} collections with status lower than CURATED..."
        )

        for collection in collections_for_delta:
            candidate_urls = CandidateURL.objects.filter(collection=collection)
            for candidate_url in candidate_urls:
                DeltaUrl.objects.create(
                    collection=candidate_url.collection,
                    url=candidate_url.url,
                    scraped_title=candidate_url.scraped_title,
                    generated_title=candidate_url.generated_title,
                    visited=candidate_url.visited,
                    document_type=candidate_url.document_type,
                    division=candidate_url.division,
                    delete=False,
                )
            self.stdout.write(
                f"Migrated {candidate_urls.count()} URLs from collection '{collection.name}' to DeltaUrl."
            )

        self.stdout.write(self.style.SUCCESS("Migration complete."))

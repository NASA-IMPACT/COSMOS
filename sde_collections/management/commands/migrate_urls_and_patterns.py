import time

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db.models import Count

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import WorkflowStatusChoices
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from sde_collections.models.pattern import (
    DivisionPattern,
    DocumentTypePattern,
    ExcludePattern,
    IncludePattern,
    TitlePattern,
)

STATUSES_TO_MIGRATE = [
    WorkflowStatusChoices.CURATED,
    WorkflowStatusChoices.QUALITY_FIXED,
    WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED,
    WorkflowStatusChoices.SECRET_DEPLOYMENT_FAILED,
    WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK,
    WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK,
    WorkflowStatusChoices.QUALITY_CHECK_FAILED,
    WorkflowStatusChoices.QUALITY_CHECK_MINOR,
    WorkflowStatusChoices.QUALITY_CHECK_PERFECT,
    WorkflowStatusChoices.PROD_PERFECT,
    WorkflowStatusChoices.PROD_MINOR,
    WorkflowStatusChoices.PROD_MAJOR,
]


class Command(BaseCommand):
    help = """Migrate CandidateURLs to DeltaUrl, apply the matching patterns,
              and then promote to CuratedUrl based on collection workflow status"""

    def handle(self, *args, **kwargs):
        # Log the start time for the entire process
        overall_start_time = time.time()
        self.stdout.write("Starting the migration process...")

        # Step 1: Clear all Delta instances
        start_time = time.time()
        DumpUrl.objects.all().delete()
        CuratedUrl.objects.all().delete()
        DeltaUrl.objects.all().delete()
        DeltaExcludePattern.objects.all().delete()
        DeltaIncludePattern.objects.all().delete()
        DeltaTitlePattern.objects.all().delete()
        DeltaDocumentTypePattern.objects.all().delete()
        DeltaDivisionPattern.objects.all().delete()
        self.stdout.write(f"Cleared all Delta instances in {time.time() - start_time:.2f} seconds.")

        # Step 2: Get collections ordered by URL count
        start_time = time.time()
        total_collections = Collection.objects.count()
        collections = Collection.objects.annotate(url_count=Count("candidate_urls")).order_by("url_count")
        self.stdout.write(f"Retrieved and ordered collections in {time.time() - start_time:.2f} seconds.")

        # Set to track URLs globally across all collections
        global_unique_urls = set()

        # Process each collection individually
        for index, collection in enumerate(collections):
            collection_start_time = time.time()
            self.stdout.write(
                f"\nProcessing collection: {collection} with {collection.url_count} URLs ({index + 1}/{total_collections})"  # noqa
            )

            # Step 3: Migrate CandidateURLs to DeltaUrl for this collection
            urls_start_time = time.time()
            delta_urls = []

            for candidate_url in CandidateURL.objects.filter(collection=collection):
                if candidate_url.url not in global_unique_urls:
                    global_unique_urls.add(candidate_url.url)
                    delta_urls.append(
                        DeltaUrl(
                            collection=candidate_url.collection,
                            url=candidate_url.url,
                            scraped_title=candidate_url.scraped_title,
                            generated_title=candidate_url.generated_title,
                            visited=candidate_url.visited,
                            document_type=candidate_url.document_type,
                            division=candidate_url.division,
                            to_delete=False,
                        )
                    )

            # Bulk create the unique DeltaUrl instances for this collection
            DeltaUrl.objects.bulk_create(delta_urls)
            self.stdout.write(
                f"Migrated {len(delta_urls)} URLs to DeltaUrl in {time.time() - urls_start_time:.2f} seconds"
            )

            # Step 4: Migrate Patterns for this collection
            patterns_start_time = time.time()

            for pattern_model in [ExcludePattern, IncludePattern, TitlePattern, DocumentTypePattern, DivisionPattern]:
                self.migrate_patterns_for_collection(pattern_model, collection)

            self.stdout.write(f"Pattern migration completed in {time.time() - patterns_start_time:.2f} seconds")

            # Step 5: Promote to CuratedUrl if applicable
            if collection.workflow_status in STATUSES_TO_MIGRATE:
                promote_start_time = time.time()
                collection.promote_to_curated()
                self.stdout.write(f"Promoted to CuratedUrl in {time.time() - promote_start_time:.2f} seconds")

            self.stdout.write(
                f"Total processing time for collection: {time.time() - collection_start_time:.2f} seconds\n"
                f"--------------------"
            )

        # Log the total time for the process
        self.stdout.write(f"Total migration process completed in {time.time() - overall_start_time:.2f} seconds.")

    def migrate_patterns_for_collection(self, non_delta_model, collection):
        """Migrate patterns from a non-delta model to the corresponding delta model for a specific collection."""
        # Determine the delta model name and fetch the model class
        delta_model_name = "Delta" + non_delta_model.__name__
        delta_model = apps.get_model(non_delta_model._meta.app_label, delta_model_name)

        # Get all field names from both models except 'id' (primary key)
        non_delta_fields = {field.name for field in non_delta_model._meta.fields if field.name != "id"}
        delta_fields = {field.name for field in delta_model._meta.fields if field.name != "id"}

        # Find shared fields
        shared_fields = non_delta_fields.intersection(delta_fields)

        # Only process patterns for the current collection
        for pattern in non_delta_model.objects.filter(collection=collection):
            # Build the dictionary of shared fields to copy
            delta_fields_data = {field: getattr(pattern, field) for field in shared_fields}

            # Create an instance of the delta model and save it to call the custom save() method
            delta_instance = delta_model(**delta_fields_data)
            delta_instance.save()  # Explicitly call save() to trigger custom logic

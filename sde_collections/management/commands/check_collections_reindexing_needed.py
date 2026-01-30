# Usage: docker-compose -f local.yml run --rm django python manage.py check_collections_reindexing_needed

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    """
    Management command to identify collections that need reindexing based on two criteria:
    1. Collections previously reindexed on prod (REINDEXING_INDEXED_ON_PROD) over 2 months ago
    2. Collections that reached PROD_PERFECT over 2 months ago and haven't been reindexed yet
    """

    help = "Identifies and marks collections that need reindexing based on time threshold"

    def handle(self, *args, **options):
        # Import models here to avoid circular imports
        from sde_collections.models.collection import (
            Collection,
            ReindexingHistory,
            WorkflowHistory,
        )
        from sde_collections.models.collection_choice_fields import (
            ReindexingStatusChoices,
            WorkflowStatusChoices,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "\n=== Collection Reindexing Check ===\n"
                f"Threshold: {settings.COLLECTION_REINDEX_INTERVAL_DAYS} days\n"
            )
        )

        threshold = timezone.now() - timedelta(days=settings.COLLECTION_REINDEX_INTERVAL_DAYS)
        collections_to_update = []

        # Case 1: Collections that were previously reindexed on prod
        prod_reindexed_collections = Collection.objects.filter(
            reindexing_status=ReindexingStatusChoices.REINDEXING_INDEXED_ON_PROD
        )

        self.stdout.write(
            f"\nChecking {prod_reindexed_collections.count()} collections that were "
            f"reindexed on prod (REINDEXING_INDEXED_ON_PROD)..."
        )

        for collection in prod_reindexed_collections:
            # Get latest reindexing history
            latest_history = ReindexingHistory.objects.filter(collection=collection).order_by("-created_at").first()

            if not latest_history or latest_history.created_at <= threshold:
                collections_to_update.append(collection)
                self.stdout.write(
                    f"Collection {collection.id} [{collection.name}] needs reindexing - "
                    f"Last Reindexed: {latest_history.created_at if latest_history else 'Never'}"
                )

        # Case 2: Collections that completed first-time indexing (PROD_PERFECT)
        first_time_collections = Collection.objects.filter(
            workflow_status=WorkflowStatusChoices.PROD_PERFECT,
            reindexing_status=ReindexingStatusChoices.REINDEXING_NOT_NEEDED,
            # We don't want to target those collections which are already going through some reindexing processes
        )

        self.stdout.write(
            f"\nChecking {first_time_collections.count()} collections that are in PROD_PERFECT workflow status..."
        )

        for collection in first_time_collections:
            # Get when collection reached PROD_PERFECT
            prod_perfect_history = (
                WorkflowHistory.objects.filter(
                    collection=collection, workflow_status=WorkflowStatusChoices.PROD_PERFECT
                )
                .order_by("-created_at")
                .first()
            )

            if not prod_perfect_history or prod_perfect_history.created_at <= threshold:
                collections_to_update.append(collection)
                self.stdout.write(
                    f"Collection {collection.id:<5} [{collection.name:<60}] needs reindexing - "
                    f"In PROD_PERFECT since: {prod_perfect_history.created_at if prod_perfect_history else 'Unknown'}"
                )

        # Show summary and ask for confirmation
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\nSummary:"
                f"\n- Total collections to update: {len(collections_to_update)}"
                f"\n- Will be marked as: {ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV.label}"
                "\n- First 5 collections will be processed in this test run"
            )
        )

        if collections_to_update:
            user_input = input("Do you want to mark these collections for reindexing? (yes/no)")

            if user_input.lower() == "yes":
                # Process first 5 collections only for testing
                for collection in collections_to_update[:5]:
                    collection.reindexing_status = ReindexingStatusChoices.REINDEXING_NEEDED_ON_DEV
                    collection.save()
                    self.stdout.write(f"✓ Marked collection: {collection.name}")

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nSuccessfully marked {len(collections_to_update[:5])} collections for reindexing"
                        "\nNote: Only processed first 5 collections in test mode"
                    )
                )
            else:
                self.stdout.write(self.style.WARNING("\nUpdate Cancelled!"))

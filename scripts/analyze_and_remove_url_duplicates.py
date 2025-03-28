from collections import defaultdict

from django.db import models

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection

# Get all field names except 'id' and 'collection' (since we're already looping by collection)
duplicate_fields = [field.name for field in CandidateURL._meta.get_fields() if field.name not in ["id", "collection"]]


def analyze_duplicates():
    """Analyze duplicates and print how many would be deleted in each collection."""
    deletion_stats = defaultdict(lambda: {"total": 0, "to_delete": 0})

    # Loop through each collection
    for collection in Collection.objects.all():
        # Count total URLs for the collection
        total_urls = CandidateURL.objects.filter(collection=collection).count()
        deletion_stats[collection.config_folder]["total"] = total_urls

        # Group CandidateURL instances by all fields dynamically
        duplicates_in_collection = (
            CandidateURL.objects.filter(collection=collection)
            .values(*duplicate_fields)
            .annotate(count=models.Count("id"))
            .filter(count__gt=1)
        )

        # Count potential deletions without deleting
        for entry in duplicates_in_collection:
            duplicates_count = CandidateURL.objects.filter(
                collection=collection, **{field: entry[field] for field in duplicate_fields}
            ).count()
            deletion_stats[collection.config_folder]["to_delete"] += duplicates_count - 1

    # Print analysis results
    print("Duplicate analysis completed.")
    for config_folder, stats in deletion_stats.items():
        print(f"{config_folder}' has {stats['total']} total URL(s), with {stats['to_delete']} duplicates.")


def delete_duplicates():
    """Delete duplicates based on previously analyzed duplicates."""
    deletion_stats = defaultdict(int)

    # Loop through each collection
    for collection in Collection.objects.all():
        # Group CandidateURL instances by all fields dynamically
        duplicates_in_collection = (
            CandidateURL.objects.filter(collection=collection)
            .values(*duplicate_fields)
            .annotate(count=models.Count("id"))
            .filter(count__gt=1)
        )

        # Delete duplicates and track deletions
        for entry in duplicates_in_collection:
            duplicates = CandidateURL.objects.filter(
                collection=collection, **{field: entry[field] for field in duplicate_fields}
            )

            # Keep the first instance and delete the rest
            for candidate in duplicates[1:]:  # Skip the first to retain it
                candidate.delete()
                deletion_stats[collection.config_folder] += 1

    # Print deletion results
    print("Duplicate URL cleanup completed.")
    for config_folder, deleted_count in deletion_stats.items():
        print(f"Collection '{config_folder}' had {deleted_count} duplicate URL(s) deleted.")


# Usage
analyze_duplicates()  # First analyze duplicates
delete_duplicates()  # Then delete duplicates based on analysis

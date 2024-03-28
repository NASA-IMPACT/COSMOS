from django.db.models import Count

from sde_collections.models.candidate_url import CandidateURL
from sde_collections.models.collection import Collection


def remove_duplicate_urls(collection_name):
    """
    Removes duplicate CandidateURL entries for a given collection name.

    Args:
    - collection_name: The name of the collection for which to remove duplicate URLs.
    """
    try:
        collection = Collection.objects.get(name=collection_name)
    except Collection.DoesNotExist:
        print(f"Collection with name '{collection_name}' does not exist.")
        return

    duplicate_urls = (
        CandidateURL.objects.filter(collection=collection)
        .values("url")
        .annotate(url_count=Count("id"))
        .filter(url_count__gt=1)
    )

    for entry in duplicate_urls:
        duplicate_entries = CandidateURL.objects.filter(collection=collection, url=entry["url"]).order_by("id")

        duplicates_to_delete = duplicate_entries.exclude(id=duplicate_entries.first().id)
        count_deleted = duplicates_to_delete.count()
        duplicates_to_delete.delete()
        print(f"Deleted {count_deleted} duplicate entries for URL '{entry['url']}'.")

    print("Completed deleting duplicated URLs...")

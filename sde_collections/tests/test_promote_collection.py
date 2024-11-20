# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_promote_collection.py

import pytest

from sde_collections.models.delta_patterns import (
    DeltaExcludePattern,
    DeltaIncludePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl
from sde_collections.tests.factories import CollectionFactory


@pytest.fixture
def collection():
    # Use the factory to create a collection with all necessary fields populated
    return CollectionFactory()


@pytest.mark.django_db
def test_initial_promotion_creates_curated_urls(collection):
    # Start with no DeltaUrls or CuratedUrls
    assert DeltaUrl.objects.filter(collection=collection).count() == 0
    assert CuratedUrl.objects.filter(collection=collection).count() == 0

    # Add new DeltaUrls to promote
    DeltaUrl.objects.create(collection=collection, url="https://example1.com", scraped_title="Title 1")
    DeltaUrl.objects.create(collection=collection, url="https://example2.com", scraped_title="Title 2")

    # Promote DeltaUrls to CuratedUrls
    collection.promote_to_curated()

    # Check that CuratedUrls were created
    curated_urls = CuratedUrl.objects.filter(collection=collection)
    assert curated_urls.count() == 2
    assert curated_urls.filter(url="https://example1.com", scraped_title="Title 1").exists()
    assert curated_urls.filter(url="https://example2.com", scraped_title="Title 2").exists()


@pytest.mark.django_db
def test_promotion_updates_existing_curated_urls(collection):
    # Dictionary containing test data for each URL
    test_data = {
        "url1": {"url": "https://example1.com", "original_title": "Title 1", "updated_title": "Updated Title 1"},
        "url2": {"url": "https://example2.com", "original_title": "Title 2", "updated_title": "Updated Title 2"},
    }

    # Create initial DeltaUrls and promote them
    for data in test_data.values():
        DeltaUrl.objects.create(collection=collection, url=data["url"], scraped_title=data["original_title"])
    collection.promote_to_curated()

    assert DeltaUrl.objects.all().count() == 0

    # Re-create DeltaUrls with updated titles
    for data in test_data.values():
        DeltaUrl.objects.create(collection=collection, url=data["url"], scraped_title=data["updated_title"])

    # Promote the updates
    collection.promote_to_curated()

    # Check that CuratedUrls were updated with the updated titles
    for data in test_data.values():
        curated_url = CuratedUrl.objects.get(url=data["url"])
        assert curated_url.scraped_title == data["updated_title"]


@pytest.mark.django_db
def test_promotion_deletes_curated_urls(collection):
    # Create initial DeltaUrls and promote them
    DeltaUrl.objects.create(collection=collection, url="https://example1.com", scraped_title="Title 1")
    DeltaUrl.objects.create(collection=collection, url="https://example2.com", scraped_title="Title 2")
    collection.promote_to_curated()

    # create a new DeltaUrl marked for deletion
    DeltaUrl.objects.create(collection=collection, url="https://example1.com", scraped_title="Title 1", to_delete=True)

    # Promote the deletion
    collection.promote_to_curated()

    # Check that the CuratedUrl for the deleted DeltaUrl was removed
    assert not CuratedUrl.objects.filter(url="https://example1.com").exists()
    # Ensure the other CuratedUrl is still present
    assert CuratedUrl.objects.filter(url="https://example2.com").exists()


@pytest.mark.django_db
def test_patterns_reapplied_after_promotion(collection):
    # Add DeltaUrls matching the patterns
    DeltaUrl.objects.create(collection=collection, url="https://exclude.com", scraped_title="Exclude This")
    DeltaUrl.objects.create(collection=collection, url="https://include.com", scraped_title="Include This")

    # Create exclude and include patterns
    exclude_pattern = DeltaExcludePattern.objects.create(
        collection=collection, match_pattern_type=2, match_pattern="exclude.*"
    )
    include_pattern = DeltaIncludePattern.objects.create(
        collection=collection, match_pattern_type=2, match_pattern="include.*"
    )

    # Promote DeltaUrls to CuratedUrls
    collection.promote_to_curated()

    # Refresh the patterns and check relationships
    exclude_pattern.refresh_from_db()
    include_pattern.refresh_from_db()

    # Verify that patterns are reapplied
    curated_urls = CuratedUrl.objects.filter(collection=collection)

    assert curated_urls.filter(url="https://exclude.com").exists()
    assert curated_urls.filter(url="https://include.com").exists()

    # Ensure exclude_pattern and include_pattern relationships are populated
    assert exclude_pattern.curated_urls.filter(url="https://exclude.com").exists()
    assert include_pattern.curated_urls.filter(url="https://include.com").exists()

    # Verify exclusion status
    assert curated_urls.filter(url="https://exclude.com", excluded=True).exists()

# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_promote_collection.py
import pytest

from sde_collections.models.delta_patterns import (
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
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


@pytest.mark.django_db
def test_promotion_with_overlapping_patterns_and_deletion():
    """Test complex scenario with multiple overlapping patterns and URL deletion."""
    collection = CollectionFactory()

    # Create a more complex set of URLs that might trigger overlapping patterns
    urls = [
        "https://example.com/docs/guide1",
        "https://example.com/docs/guide2",
        "https://example.com/api/v1/doc1",
        "https://example.com/api/v1/doc2",
    ]

    # Create initial DeltaUrls
    for url in urls:
        DeltaUrl.objects.create(collection=collection, url=url, scraped_title=f"Title for {url}")

    # Create overlapping patterns that will affect the same URLs
    patterns = [
        {"pattern": ".*docs.*", "title": "Documentation: {title}"},
        {"pattern": ".*guide.*", "title": "Guide: {title}"},
        {"pattern": ".*api.*", "title": "API: {title}"},
        {"pattern": ".*doc[0-9]", "title": "Doc Number: {title}"},
    ]

    # Create and apply multiple patterns
    title_patterns = []
    for p in patterns:
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern=p["pattern"],
            match_pattern_type=2,  # Multi-URL Pattern
            title_pattern=p["title"],
        )
        pattern.apply()
        title_patterns.append(pattern)

    # Initial promotion
    collection.promote_to_curated()

    # Verify our complex setup
    for pattern in title_patterns:
        matching_urls = pattern.curated_urls.all()
        print(f"\nPattern '{pattern.match_pattern}' matches {matching_urls.count()} URLs:")
        for url in matching_urls:
            print(f"- {url.url}")

    # Now create deletion DeltaUrls but with overlapping pattern matches
    urls_to_delete = ["https://example.com/docs/guide1", "https://example.com/api/v1/doc1"]
    for url in urls_to_delete:
        DeltaUrl.objects.create(collection=collection, url=url, to_delete=True)

    # Try the promotion - this should trigger similar conditions to production
    collection.promote_to_curated()

    # Print final state for debugging
    print("\nFinal state:")
    for pattern in title_patterns:
        print(f"\nPattern '{pattern.match_pattern}':")
        for url in pattern.curated_urls.all():
            print(f"- {url.url}")


@pytest.mark.django_db
def test_promotion_with_title_change():
    """Test updating a CuratedUrl that has active title pattern relationships."""
    collection = CollectionFactory()

    # Create initial DeltaUrl and promote it
    url = "https://example.com/doc1"
    DeltaUrl.objects.create(collection=collection, url=url, scraped_title="Original Title")

    # Create and apply a title pattern
    pattern = DeltaTitlePattern.objects.create(
        collection=collection, match_pattern=".*doc1", match_pattern_type=2, title_pattern="Pattern: {title}"
    )
    pattern.apply()

    # Initial promotion
    collection.promote_to_curated()

    # Verify pattern relationship exists
    curated = CuratedUrl.objects.get(url=url)
    assert pattern.curated_urls.filter(id=curated.id).exists()

    # Now create new DeltaUrl with updated title
    DeltaUrl.objects.create(collection=collection, url=url, scraped_title="New Title")  # Changed title

    # This should trigger the same error we're seeing in production
    collection.promote_to_curated()

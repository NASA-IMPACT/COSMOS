# noqa: F841
# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_migrate_dump.py

import pytest

from sde_collections.models.collection_choice_fields import DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)

DELTA_COMPARISON_FIELDS = ["scraped_title"]  # Assuming a central definition


@pytest.mark.django_db
class TestMigrationHelpers:
    def test_clear_delta_urls(self):
        collection = CollectionFactory()
        DeltaUrlFactory.create_batch(5, collection=collection)
        collection.clear_delta_urls()
        assert DeltaUrl.objects.filter(collection=collection).count() == 0

    def test_clear_dump_urls(self):
        collection = CollectionFactory()
        DumpUrlFactory.create_batch(5, collection=collection)
        collection.clear_dump_urls()
        assert DumpUrl.objects.filter(collection=collection).count() == 0

    def test_create_or_update_delta_url_add(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        collection.create_or_update_delta_url(dump_url, to_delete=False)
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.to_delete is False
        for field in DELTA_COMPARISON_FIELDS:
            assert getattr(delta, field) == getattr(dump_url, field)

    def test_create_or_update_delta_url_delete(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)
        collection.create_or_update_delta_url(curated_url, to_delete=True)
        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.to_delete is True
        assert delta.scraped_title == curated_url.scraped_title


@pytest.mark.django_db
class TestMigrateDumpToDelta:
    def test_new_url_in_dump_only(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.to_delete is False
        for field in DELTA_COMPARISON_FIELDS:
            assert getattr(delta, field) == getattr(dump_url, field)

    def test_url_in_both_with_different_field(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="New Title")
        CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Old Title")
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.to_delete is False
        assert delta.scraped_title == "New Title"

    def test_url_in_curated_only(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.to_delete is True
        assert delta.scraped_title == curated_url.scraped_title

    def test_identical_url_in_both(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="Same Title")
        CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Same Title")
        collection.migrate_dump_to_delta()
        assert not DeltaUrl.objects.filter(url=dump_url.url).exists()

    def test_full_migration_flow(self):
        collection = CollectionFactory()
        dump_url_new = DumpUrlFactory(collection=collection)  # New URL
        dump_url_update = DumpUrlFactory(collection=collection, scraped_title="Updated Title")
        CuratedUrlFactory(collection=collection, url=dump_url_update.url, scraped_title="Old Title")
        curated_url_delete = CuratedUrlFactory(collection=collection)  # Missing in Dump

        collection.migrate_dump_to_delta()

        # New URL moved to DeltaUrls
        assert DeltaUrl.objects.filter(url=dump_url_new.url, to_delete=False).exists()

        # Updated URL moved to DeltaUrls
        delta_update = DeltaUrl.objects.get(url=dump_url_update.url)
        assert delta_update.scraped_title == "Updated Title"
        assert delta_update.to_delete is False

        # Deleted URL in CuratedUrls marked as delete in DeltaUrls
        delta_delete = DeltaUrl.objects.get(url=curated_url_delete.url)
        assert delta_delete.to_delete is True

    def test_empty_collections(self):
        collection = CollectionFactory()
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(collection=collection).count() == 0

    def test_partial_data_in_dump_urls(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="")
        collection.migrate_dump_to_delta()
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.scraped_title == ""
        assert delta.to_delete is False


@pytest.mark.django_db
class TestMigrationIdempotency:
    def test_migrate_dump_to_delta_idempotency(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)
        CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Different Title")

        # First migration run
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1

        # Run migration again
        collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1  # Ensure no duplicates

    def test_create_or_update_delta_url_idempotency(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)

        # First call
        collection.create_or_update_delta_url(dump_url, to_delete=False)
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1

        # Second call with the same data
        collection.create_or_update_delta_url(dump_url, to_delete=False)
        assert DeltaUrl.objects.filter(url=dump_url.url).count() == 1  # Should still be one


@pytest.mark.django_db
def test_create_or_update_delta_url_field_copy():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(
        collection=collection,
        scraped_title="Test Title",
        scraped_text="Test Text",
        generated_title="Generated Test Title",
        visited=True,
        document_type=1,
        division=2,
    )

    collection.create_or_update_delta_url(dump_url, to_delete=False)
    delta = DeltaUrl.objects.get(url=dump_url.url)

    # Verify each field is copied correctly
    for field in DumpUrl._meta.fields:
        if field.name not in ["id", "collection", "url"]:
            assert getattr(delta, field.name) == getattr(dump_url, field.name)


@pytest.mark.django_db
class TestGranularFullMigrationFlow:
    def test_full_migration_new_url(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection)  # New URL
        collection.migrate_dump_to_delta()

        # New URL should be added to DeltaUrls
        assert DeltaUrl.objects.filter(url=dump_url.url, to_delete=False).exists()

    def test_full_migration_updated_url(self):
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, scraped_title="Updated Title")
        collection.migrate_dump_to_delta()

        # URL with differing fields should be updated in DeltaUrls
        delta_update = DeltaUrl.objects.get(url=dump_url.url)
        assert delta_update.scraped_title == "Updated Title"
        assert delta_update.to_delete is False

    def test_full_migration_deleted_url(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection)  # URL to be deleted
        collection.migrate_dump_to_delta()

        # Missing URL in DumpUrls should be marked as delete in DeltaUrls
        delta_delete = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_delete.to_delete is True


@pytest.mark.django_db
def test_empty_delta_comparison_fields():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(collection=collection, scraped_title="Same Title")
    CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="Same Title")  # noqa

    global DELTA_COMPARISON_FIELDS
    original_fields = DELTA_COMPARISON_FIELDS
    DELTA_COMPARISON_FIELDS = []  # Simulate empty comparison fields

    try:
        collection.migrate_dump_to_delta()
        # No DeltaUrl should be created as there are no fields to compare
        assert not DeltaUrl.objects.filter(url=dump_url.url).exists()
    finally:
        DELTA_COMPARISON_FIELDS = original_fields  # Reset the fields after test


@pytest.mark.django_db
def test_partial_data_in_curated_urls():
    collection = CollectionFactory()
    dump_url = DumpUrlFactory(collection=collection, scraped_title="Title Exists")
    CuratedUrlFactory(collection=collection, url=dump_url.url, scraped_title="")  # noqa

    collection.migrate_dump_to_delta()

    # Since `scraped_title` differs (None vs "Title Exists"), it should create a DeltaUrl
    delta = DeltaUrl.objects.get(url=dump_url.url)
    assert delta.scraped_title == "Title Exists"
    assert delta.to_delete is False


@pytest.mark.django_db
def test_full_migration_with_patterns():
    """
    Test a complete migration flow with exclude patterns and document type patterns.
    Tests the following scenarios:
    - New URL from dump (should create delta)
    - Updated URL from dump (should create delta with new title)
    - Deleted URL (should create delta marked for deletion)
    - URL matching exclude pattern (should be excluded)
    - URL matching document type pattern (should have correct doc type)
    """
    collection = CollectionFactory()

    # Set up initial DumpUrls and CuratedUrls
    DumpUrlFactory(collection=collection, url="https://example.com/new", scraped_title="New Page")
    DumpUrlFactory(collection=collection, url="https://example.com/update", scraped_title="Updated Title")
    DumpUrlFactory(collection=collection, url="https://example.com/docs/guide", scraped_title="Documentation Guide")

    CuratedUrlFactory(collection=collection, url="https://example.com/update", scraped_title="Old Title")
    CuratedUrlFactory(collection=collection, url="https://example.com/delete", scraped_title="Delete Me")
    CuratedUrlFactory(collection=collection, url="https://example.com/docs/guide", scraped_title="Documentation Guide")

    # Create patterns before migration
    exclude_pattern = DeltaExcludePattern.objects.create(
        collection=collection,
        match_pattern="https://example.com/delete",
        match_pattern_type=1,  # Individual URL
        reason="Test exclusion",
    )

    doc_type_pattern = DeltaDocumentTypePattern.objects.create(
        collection=collection,
        match_pattern="https://example.com/docs/*",
        match_pattern_type=2,  # Multi-URL pattern
        document_type=DocumentTypes.DOCUMENTATION,
    )

    # Perform migration
    collection.migrate_dump_to_delta()

    # 1. Check new URL was created as delta
    new_delta = DeltaUrl.objects.get(url="https://example.com/new")
    assert new_delta.to_delete is False
    assert new_delta.scraped_title == "New Page"

    # 2. Check updated URL has new title in delta
    update_delta = DeltaUrl.objects.get(url="https://example.com/update")
    assert update_delta.to_delete is False
    assert update_delta.scraped_title == "Updated Title"

    # 3. Check deleted URL is marked for deletion
    delete_delta = DeltaUrl.objects.get(url="https://example.com/delete")
    assert delete_delta.to_delete is True
    assert delete_delta.excluded is True  # Should be excluded due to pattern

    # 4. Check documentation URL has correct type
    docs_delta = DeltaUrl.objects.get(url="https://example.com/docs/guide")
    assert docs_delta.document_type == DocumentTypes.DOCUMENTATION
    assert docs_delta.to_delete is False

    # 5. Verify pattern relationships
    exclude_pattern.refresh_from_db()
    doc_type_pattern.refresh_from_db()

    assert exclude_pattern.delta_urls.filter(url="https://example.com/delete").exists()
    assert doc_type_pattern.delta_urls.filter(url="https://example.com/docs/guide").exists()

    # 6. Check total number of deltas is correct
    assert DeltaUrl.objects.filter(collection=collection).count() == 4

    # Optional: Test promotion to verify patterns stick
    collection.promote_to_curated()

    # Verify results after promotion
    assert not CuratedUrl.objects.filter(url="https://example.com/delete").exists()
    assert CuratedUrl.objects.get(url="https://example.com/docs/guide").document_type == DocumentTypes.DOCUMENTATION
    assert CuratedUrl.objects.get(url="https://example.com/update").scraped_title == "Updated Title"
    assert not CuratedUrl.objects.filter(scraped_title="Old Title").exists()

# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_migration.py

import pytest
from django.test import TestCase

from sde_collections.models.collection_choice_fields import Divisions, DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
)
from sde_collections.models.delta_url import DeltaUrl, DumpUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)


@pytest.mark.django_db
class TestMigrateDumpToDelta(TestCase):
    """Test the migrate_dump_to_delta process comprehensively."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_basic_migration_new_url(self):
        """Test basic migration of a new URL with no existing curated version."""
        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/new",
            scraped_title="New Doc",
            document_type=DocumentTypes.DOCUMENTATION,
            division=Divisions.ASTROPHYSICS,
        )

        self.collection.migrate_dump_to_delta()

        # Verify delta created with all fields
        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.scraped_title == dump_url.scraped_title
        assert delta.document_type == dump_url.document_type
        assert delta.division == dump_url.division
        assert delta.to_delete is False

    def test_migration_with_differing_curated(self):
        """Test migration when dump differs from existing curated URL."""
        url = "https://example.com/doc"

        dump_url = DumpUrlFactory(
            collection=self.collection,
            url=url,
            scraped_title="New Title",
            document_type=DocumentTypes.DATA,
        )

        CuratedUrlFactory(
            collection=self.collection,
            url=url,
            scraped_title="Old Title",
            document_type=DocumentTypes.DOCUMENTATION,
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=url)
        assert delta.scraped_title == dump_url.scraped_title
        assert delta.document_type == dump_url.document_type
        assert delta.to_delete is False

    def test_migration_marks_missing_urls_for_deletion(self):
        """Test that curated URLs not in dump are marked for deletion."""
        # Create only curated URL, no dump
        curated_url = CuratedUrlFactory(
            collection=self.collection,
            url="https://example.com/old",
            scraped_title="Old Doc",
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.to_delete is True
        assert delta.scraped_title == curated_url.scraped_title

    def test_migration_handles_null_fields(self):
        """Test migration properly handles null/empty fields."""
        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/doc",
            scraped_title="",  # Empty string
            document_type=None,  # Null
            division=None,  # Null
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.scraped_title == ""
        assert delta.document_type is None
        assert delta.division is None

    def test_migration_clears_existing_deltas(self):
        """Test that existing deltas are cleared before migration."""
        # Create pre-existing delta
        old_delta = DeltaUrlFactory(
            collection=self.collection,
            url="https://example.com/old",
            scraped_title="Old Delta",
        )

        # Create new dump URL
        new_dump = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/new",
            scraped_title="New Dump",
        )

        self.collection.migrate_dump_to_delta()

        # Verify old delta is gone and only new one exists
        assert not DeltaUrl.objects.filter(url=old_delta.url).exists()
        assert DeltaUrl.objects.filter(url=new_dump.url).exists()

    def test_migration_with_exclude_pattern(self):
        """Test migration interacts correctly with exclude patterns."""
        # Create pattern first
        DeltaExcludePattern.objects.create(
            collection=self.collection,
            match_pattern="*internal*",
            match_pattern_type=DeltaExcludePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        # Create dump URL that should be excluded
        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/internal/doc",
            scraped_title="Internal Doc",
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.excluded is True

    def test_migration_with_field_modifying_pattern(self):
        """Test migration with patterns that modify fields."""
        # Create document type pattern
        DeltaDocumentTypePattern.objects.create(
            collection=self.collection,
            match_pattern="*.pdf",
            match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            document_type=DocumentTypes.DATA,
        )

        # Create division pattern
        DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="*/astro/*",
            match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            division=Divisions.ASTROPHYSICS,
        )

        # Create dump URL that matches both patterns
        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/astro/data.pdf",
            scraped_title="Astro Data",
            document_type=DocumentTypes.DOCUMENTATION,  # Different from pattern
            division=Divisions.EARTH_SCIENCE,  # Different from pattern
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert delta.document_type == DocumentTypes.DATA
        assert delta.division == Divisions.ASTROPHYSICS

    def test_migration_with_multiple_urls(self):
        """Test migration with multiple URLs in various states."""
        # Create mix of dump and curated URLs
        dump_urls = [DumpUrlFactory(collection=self.collection) for _ in range(3)]
        curated_urls = [CuratedUrlFactory(collection=self.collection) for _ in range(2)]

        self.collection.migrate_dump_to_delta()

        # Should have deltas for all dump URLs
        for dump_url in dump_urls:
            assert DeltaUrl.objects.filter(url=dump_url.url, to_delete=False).exists()

        # Should have deletion deltas for curated URLs not in dump
        for curated_url in curated_urls:
            assert DeltaUrl.objects.filter(url=curated_url.url, to_delete=True).exists()

    def test_migration_with_empty_states(self):
        """Test migration handles empty dump and curated states."""
        # No dump or curated URLs exist
        self.collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.count() == 0

        # Only curated URLs exist
        CuratedUrlFactory(collection=self.collection)
        self.collection.migrate_dump_to_delta()
        assert DeltaUrl.objects.count() == 1
        assert DeltaUrl.objects.first().to_delete is True

    def test_migration_preserves_all_fields(self):
        """Test that ALL fields are preserved during migration, not just changed ones."""
        # Create dump URL with all fields populated
        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/doc",
            scraped_title="Title",
            scraped_text="Full text content",
            generated_title="Generated Title",
            document_type=DocumentTypes.DOCUMENTATION,
            division=Divisions.ASTROPHYSICS,
            visited=True,
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=dump_url.url)

        # Verify all fields were copied
        fields_to_check = [
            "scraped_title",
            "scraped_text",
            "generated_title",
            "document_type",
            "division",
            "visited",
        ]

        for field in fields_to_check:
            assert getattr(delta, field) == getattr(dump_url, field)

    def test_clearing_dump_urls(self):
        """Test that dump URLs are cleared after migration."""
        DumpUrlFactory(collection=self.collection)
        DumpUrlFactory(collection=self.collection)

        self.collection.migrate_dump_to_delta()

        assert DumpUrl.objects.filter(collection=self.collection).count() == 0

    def test_pattern_relationships_updated(self):
        """Test that pattern relationships are properly updated after migration."""
        pattern = DeltaExcludePattern.objects.create(
            collection=self.collection,
            match_pattern="*test*",
            match_pattern_type=DeltaExcludePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        dump_url = DumpUrlFactory(
            collection=self.collection,
            url="https://example.com/test/doc",
        )

        self.collection.migrate_dump_to_delta()

        delta = DeltaUrl.objects.get(url=dump_url.url)
        assert pattern.delta_urls.filter(id=delta.id).exists()

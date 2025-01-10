# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_field_modifier_unapply.py

from django.test import TestCase

from sde_collections.models.collection_choice_fields import Divisions, DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl

from .factories import CollectionFactory, DumpUrlFactory


class TestDeltaPatternUnapplyLogic(TestCase):
    """Test complete lifecycle of pattern application and removal."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_dump_to_delta_migration_with_pattern_lifecycle(self):
        """
        Test complete lifecycle:
        1. Create dump URLs
        2. Migrate to delta URLs
        3. Apply patterns
        4. Promote to curated
        5. Delete pattern
        6. Verify deltas are created
        7. Promote to curated
        8. Verify curated URLs have division set to None
        """
        # Create initial dump URLs
        [
            DumpUrlFactory(
                collection=self.collection,
                url=f"https://example.com/science/data{i}.html",
            )
            for i in range(3)
        ]

        # Migrate dump to delta
        self.collection.migrate_dump_to_delta()

        # Verify dump URLs were migrated to delta URLs
        self.assertEqual(DeltaUrl.objects.count(), 3)
        self.assertEqual(DumpUrl.objects.count(), 0)

        # Apply division pattern
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/science/*.html",
            match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            division=Divisions.BIOLOGY,
        )

        # Verify pattern was applied to existing deltas
        for delta_url in DeltaUrl.objects.all():
            self.assertEqual(delta_url.division, Divisions.BIOLOGY)

        # Promote to curated
        self.collection.promote_to_curated()

        # Verify promotion
        self.assertEqual(CuratedUrl.objects.count(), 3)
        self.assertEqual(DeltaUrl.objects.count(), 0)
        for curated_url in CuratedUrl.objects.all():
            self.assertEqual(curated_url.division, Divisions.BIOLOGY)

        # Remove pattern
        pattern.delete()

        # Should have created new deltas for all URLs setting division to None
        self.assertEqual(DeltaUrl.objects.count(), 3)
        for delta_url in DeltaUrl.objects.all():
            self.assertIsNone(delta_url.division)

        # Promote to curated
        self.collection.promote_to_curated()

        # Should updated all Curated setting division to None
        self.assertEqual(CuratedUrl.objects.count(), 3)
        for delta_url in CuratedUrl.objects.all():
            self.assertIsNone(delta_url.division)

    # Test for README_UNNAPLY_LOGIC.md Case 1: Delta Only (New URL)
    def test_pattern_removal_with_delta_only(self):
        """Test pattern removal when delta exists without corresponding curated URL."""
        # Create initial delta URL (simulating a new URL)
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/new.html")

        # Create and apply pattern
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, division=Divisions.BIOLOGY
        )

        # Verify pattern was applied
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.division, Divisions.BIOLOGY)

        # Remove pattern
        pattern.delete()

        # Verify delta still exists but with division set to None
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertIsNone(delta_url.division)
        self.assertEqual(DeltaUrl.objects.count(), 1)

    # Test for README_UNNAPLY_LOGIC.md Case 2: Delta Created to Apply Pattern
    def test_pattern_removal_with_simple_delta(self):
        """Test pattern removal when delta was created just to apply pattern."""
        # Create initial curated URL
        curated_url = CuratedUrl.objects.create(
            collection=self.collection, url="https://example.com/doc.html", division=None
        )

        # Create and apply pattern
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.BIOLOGY
        )

        # Verify delta was created with pattern's value
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertEqual(delta_url.division, Divisions.BIOLOGY)

        # Remove pattern
        pattern.delete()

        # Verify delta was deleted since it would match curated
        self.assertEqual(DeltaUrl.objects.filter(url=curated_url.url).count(), 0)

    # Test for README_UNNAPLY_LOGIC.md Case 3: Pre-existing Delta
    def test_pattern_removal_preserves_other_changes(self):
        """Test pattern removal when delta has other changes that should be preserved."""
        # Create curated URL
        curated_url = CuratedUrl.objects.create(
            collection=self.collection,
            url="https://example.com/doc.html",
            division=None,
            scraped_title="Original Title",
        )

        # Create delta with modified title
        delta_url = DeltaUrl.objects.create(
            collection=self.collection, url=curated_url.url, division=None, scraped_title="Modified Title"
        )

        # Create and apply pattern
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.BIOLOGY
        )

        # Verify pattern was applied while preserving title
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertEqual(delta_url.division, Divisions.BIOLOGY)
        self.assertEqual(delta_url.scraped_title, "Modified Title")

        # Remove pattern
        pattern.delete()

        # Verify delta still exists with original changes but pattern effect removed
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertIsNone(delta_url.division)
        self.assertEqual(delta_url.scraped_title, "Modified Title")

    # Test for README_UNNAPLY_LOGIC.md Case 4: Multiple Pattern Effects
    def test_pattern_removal_with_multiple_patterns(self):
        """Test removal of one pattern when URL is affected by multiple patterns."""
        # Create curated URL
        curated_url = CuratedUrl.objects.create(collection=self.collection, url="https://example.com/doc.html")

        # Create two patterns affecting the same URL
        division_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.BIOLOGY
        )

        DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, document_type=DocumentTypes.DATA
        )

        # Verify both patterns were applied
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertEqual(delta_url.division, Divisions.BIOLOGY)
        self.assertEqual(delta_url.document_type, DocumentTypes.DATA)

        # Remove division pattern
        division_pattern.delete()

        # Verify delta still exists with doc type but division removed
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertIsNone(delta_url.division)
        self.assertEqual(delta_url.document_type, DocumentTypes.DATA)

    # Test for Case 5: Overlapping Patterns, Specific Deleted
    def test_specific_pattern_removal_with_overlapping_patterns(self):
        """Test removal of specific pattern when more general pattern exists."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/docs/api/v2/spec.html")

        # Create general pattern
        DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/*.html",
            match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            division=Divisions.BIOLOGY,
        )

        # Create specific pattern
        specific_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, division=Divisions.ASTROPHYSICS
        )

        # Verify specific pattern took precedence
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.division, Divisions.ASTROPHYSICS)

        # Remove specific pattern
        specific_pattern.delete()

        # Verify general pattern now applies
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.division, Divisions.BIOLOGY)

    # Test for Case 6: Overlapping Patterns, General Deleted
    def test_general_pattern_removal_with_overlapping_patterns(self):
        """Test removal of general pattern when more specific pattern exists."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/docs/api/v2/spec.html")

        # Create general pattern
        general_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/*.html",
            match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            division=Divisions.BIOLOGY,
        )

        # Create specific pattern
        DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, division=Divisions.ASTROPHYSICS
        )

        # Verify specific pattern takes precedence
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.division, Divisions.ASTROPHYSICS)

        # Remove general pattern
        general_pattern.delete()

        # Verify specific pattern still applies
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.division, Divisions.ASTROPHYSICS)

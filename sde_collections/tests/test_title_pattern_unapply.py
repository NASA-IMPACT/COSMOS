# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_title_pattern_unapply.py

from django.test import TestCase

from sde_collections.models.delta_patterns import (
    DeltaResolvedTitle,
    DeltaResolvedTitleError,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl

from .factories import CollectionFactory, DumpUrlFactory


class TestTitlePatternUnapplyLogic(TestCase):
    """Test complete lifecycle of title pattern application and removal."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_dump_to_delta_migration_with_pattern_lifecycle(self):
        """
        Test complete lifecycle:
        1. Create dump URLs
        2. Migrate to delta URLs
        3. Apply title pattern
        4. Promote to curated
        5. Delete pattern
        6. Verify deltas are created
        7. Promote to curated
        8. Verify curated URLs have empty generated titles
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

        # Apply title pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/science/*.html",
            match_pattern_type=DeltaTitlePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            title_pattern="Science Document {url}",
        )

        # Verify pattern was applied to all deltas and resolution tracked
        for delta_url in DeltaUrl.objects.all():
            self.assertTrue(delta_url.generated_title.startswith("Science Document"))
            self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=pattern).exists())

        # Promote to curated
        self.collection.promote_to_curated()

        # Verify promotion
        self.assertEqual(CuratedUrl.objects.count(), 3)
        self.assertEqual(DeltaUrl.objects.count(), 0)
        for curated_url in CuratedUrl.objects.all():
            self.assertTrue(curated_url.generated_title.startswith("Science Document"))

        # Remove pattern
        pattern.delete()

        # Verify new deltas created with empty titles
        self.assertEqual(DeltaUrl.objects.count(), 3)
        for delta_url in DeltaUrl.objects.all():
            self.assertEqual(delta_url.generated_title, "")

        # Verify resolution tracking cleared
        self.assertEqual(DeltaResolvedTitle.objects.count(), 0)
        self.assertEqual(DeltaResolvedTitleError.objects.count(), 0)

    def test_pattern_removal_with_delta_only(self):
        """Test pattern removal when delta exists without corresponding curated URL."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/new.html")

        # Create and apply pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, title_pattern="New Document {url}"
        )

        # Verify pattern was applied
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("New Document"))
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=pattern).exists())

        # Remove pattern
        pattern.delete()

        # Verify delta still exists but with empty title
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.generated_title, "")
        self.assertEqual(DeltaResolvedTitle.objects.count(), 0)

    def test_pattern_removal_with_simple_delta(self):
        """Test pattern removal when delta was created just to apply pattern."""
        # Create initial curated URL
        curated_url = CuratedUrl.objects.create(
            collection=self.collection, url="https://example.com/doc.html", generated_title=""
        )

        # Create and apply pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, title_pattern="Documentation {url}"
        )

        # Verify delta was created with pattern's title
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertTrue(delta_url.generated_title.startswith("Documentation"))
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=pattern).exists())

        # Remove pattern
        pattern.delete()

        # Verify delta was deleted since it would match curated
        self.assertEqual(DeltaUrl.objects.filter(url=curated_url.url).count(), 0)
        self.assertEqual(DeltaResolvedTitle.objects.count(), 0)

    def test_pattern_removal_preserves_other_changes(self):
        """Test pattern removal when delta has other changes that should be preserved."""
        # Create curated URL
        curated_url = CuratedUrl.objects.create(
            collection=self.collection,
            url="https://example.com/doc.html",
            generated_title="",
            scraped_title="Original Title",
        )

        # Create delta with modified title
        delta_url = DeltaUrl.objects.create(
            collection=self.collection, url=curated_url.url, generated_title="", scraped_title="Modified Title"
        )

        # Create and apply pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, title_pattern="API Doc {url}"
        )

        # Verify pattern was applied while preserving scraped title
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertTrue(delta_url.generated_title.startswith("API Doc"))
        self.assertEqual(delta_url.scraped_title, "Modified Title")

        # Remove pattern
        pattern.delete()

        # Verify delta still exists with original changes but pattern effect removed
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        self.assertEqual(delta_url.generated_title, "")
        self.assertEqual(delta_url.scraped_title, "Modified Title")

    def test_pattern_removal_with_multiple_patterns(self):
        """Test removal of one pattern when URL is affected by multiple patterns."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/doc.html")

        # Create specific pattern
        specific_pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, title_pattern="Specific Title {url}"
        )

        # Create another pattern for the same URL
        generic_pattern = DeltaTitlePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/*.html",
            match_pattern_type=DeltaTitlePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            title_pattern="Generic Title {url}",
        )

        # Verify specific pattern takes precedence
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("Specific Title"))

        # Verify resolution tracking
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=specific_pattern).exists())

        # Remove specific pattern
        specific_pattern.delete()

        # Verify general pattern is now applied
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("Generic Title"))

        # Verify resolution tracking updated
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=generic_pattern).exists())

    def test_specific_pattern_removal_with_overlapping_patterns(self):
        """Test removal of specific pattern when more general pattern exists."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/docs/api/v2/spec.html")

        # Create general pattern
        DeltaTitlePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/*.html",
            match_pattern_type=DeltaTitlePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            title_pattern="General Document {url}",
        )

        # Create specific pattern
        specific_pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, title_pattern="API Spec {url}"
        )

        # Verify specific pattern took precedence
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("API Spec"))

        # Remove specific pattern
        specific_pattern.delete()

        # Verify general pattern now applies
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("General Document"))

    def test_general_pattern_removal_with_overlapping_patterns(self):
        """Test removal of general pattern when more specific pattern exists."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/docs/api/v2/spec.html")

        # Create general pattern
        general_pattern = DeltaTitlePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/*.html",
            match_pattern_type=DeltaTitlePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            title_pattern="General Document {url}",
        )

        # Create specific pattern
        specific_pattern = DeltaTitlePattern.objects.create(
            collection=self.collection, match_pattern=delta_url.url, title_pattern="API Spec {url}"
        )

        # Verify specific pattern takes precedence
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("API Spec"))

        # Verify correct resolution tracking
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=specific_pattern).exists())

        # Remove general pattern
        general_pattern.delete()

        # Verify specific pattern still applies
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertTrue(delta_url.generated_title.startswith("API Spec"))

        # Verify resolution tracking unchanged
        self.assertTrue(DeltaResolvedTitle.objects.filter(delta_url=delta_url, title_pattern=specific_pattern).exists())

    def test_pattern_removal_with_title_error(self):
        """Test handling of title resolution errors during pattern removal."""
        # Create initial delta URL
        delta_url = DeltaUrl.objects.create(collection=self.collection, url="https://example.com/doc.html")

        # Create pattern that will cause error (invalid template)
        pattern = DeltaTitlePattern.objects.create(
            collection=self.collection,
            match_pattern=delta_url.url,
            title_pattern="{invalid}",  # This should cause an error
        )

        # Verify error was recorded
        self.assertTrue(DeltaResolvedTitleError.objects.filter(delta_url=delta_url, title_pattern=pattern).exists())

        # Remove pattern
        pattern.delete()

        # Verify error tracking cleared
        self.assertEqual(DeltaResolvedTitleError.objects.count(), 0)

        # Verify delta has empty title
        delta_url = DeltaUrl.objects.get(url=delta_url.url)
        self.assertEqual(delta_url.generated_title, "")

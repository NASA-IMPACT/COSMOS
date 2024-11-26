# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_exclude_patterns.py

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase

from sde_collections.models.delta_patterns import DeltaExcludePattern
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl

from .factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)


class BaseCollectionTest(TestCase):
    def setUp(self):
        super().setUp()
        self.collection = CollectionFactory()

        # Ensure ContentTypes are created for all pattern models
        ContentType.objects.get_or_create(
            app_label="sde_collections",
            model="deltaexcludepattern",
        )
        ContentType.objects.get_or_create(
            app_label="sde_collections",
            model="deltaincludepattern",
        )
        ContentType.objects.get_or_create(
            app_label="sde_collections",
            model="deltatitlepattern",
        )
        ContentType.objects.get_or_create(
            app_label="sde_collections",
            model="deltadocumenttypepattern",
        )
        ContentType.objects.get_or_create(
            app_label="sde_collections",
            model="deltadivisionpattern",
        )


@pytest.mark.django_db
class TestDeltaExcludePatternBasics(TestCase):
    """Test basic functionality of exclude patterns."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_create_simple_exclude_pattern(self):
        """Test creation of a basic exclude pattern."""
        pattern = DeltaExcludePattern.objects.create(
            collection=self.collection, match_pattern="https://example.com/exclude-me", reason="Test exclusion"
        )
        assert pattern.match_pattern_type == DeltaExcludePattern.MatchPatternTypeChoices.INDIVIDUAL_URL

    def test_exclude_single_curated_url(self):
        """Test excluding a single curated URL creates appropriate delta."""
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/exclude-me", scraped_title="Test Title"
        )

        pattern = DeltaExcludePattern.objects.create(collection=self.collection, match_pattern=curated_url.url)

        # Pattern should create a delta URL
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url is not None
        assert pattern.delta_urls.filter(id=delta_url.id).exists()
        assert not pattern.curated_urls.filter(id=curated_url.id).exists()

    def test_exclude_single_curated_url_multiple_applies(self):
        """
        Test excluding a single curated URL creates appropriate delta.
        even if the pattern is applied multiple times
        """
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/exclude-me", scraped_title="Test Title"
        )

        pattern = DeltaExcludePattern.objects.create(collection=self.collection, match_pattern=curated_url.url)
        pattern.save()
        pattern.apply()
        pattern.apply()
        pattern.save()

        # Pattern should create a delta URL
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url is not None
        assert pattern.delta_urls.filter(id=delta_url.id).exists()
        assert not pattern.curated_urls.filter(id=curated_url.id).exists()

    def test_wildcard_pattern_exclusion(self):
        """Test excluding multiple URLs with wildcard pattern."""
        # Create multiple curated URLs
        urls = [
            CuratedUrlFactory(
                collection=self.collection,
                url=f"https://example.com/docs/internal/{i}",
                scraped_title=f"Internal Doc {i}",
            )
            for i in range(3)
        ]

        pattern = DeltaExcludePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/internal/*",
            match_pattern_type=DeltaExcludePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        # All URLs should have corresponding deltas
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 3
        for url in urls:
            assert pattern.delta_urls.filter(url=url.url).exists()
            assert not pattern.curated_urls.filter(id=url.id).exists()

    def test_exclusion_selectivity(self):
        """
        new patterns should only exclude DeltaUrls, not CuratedUrls
        """
        curated_url = CuratedUrlFactory(collection=self.collection, url="https://example.com/page/1")
        delta_url = DeltaUrlFactory(collection=self.collection, url="https://example.com/page/2")

        # confirm they both start as not excluded
        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is False
        assert CuratedUrl.objects.get(pk=curated_url.pk).excluded is False

        # Create an exclusion pattern matches both urls
        pattern = DeltaExcludePattern.objects.create(
            collection=self.collection, match_pattern="*page*", match_pattern_type=2
        )
        pattern.apply()

        # curated urls should not be affected by patterns until the collection is promoted
        # curated should be included, but delta should be excluded
        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is True
        assert CuratedUrl.objects.get(pk=curated_url.pk).excluded is False


class TestDeltaExcludePatternWorkflow(BaseCollectionTest):
    """Test complex workflows involving exclude patterns."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_pattern_removal_creates_reversal_deltas(self):
        """
        Test that removing an exclude pattern after promotion creates delta URLs
        to reverse the exclusion of previously excluded curated URLs.
        """
        collection = self.collection
        # Create curated URL
        curated_url = CuratedUrlFactory(
            collection=collection, url="https://example.com/test", scraped_title="Test Title"
        )

        # Create exclude pattern - this should create excluded delta URL
        pattern = DeltaExcludePattern.objects.create(collection=collection, match_pattern=curated_url.url)

        # Verify delta URL was created and is excluded
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.excluded is True

        # Promote collection - this should convert excluded delta URL to excluded curated URL
        collection.promote_to_curated()

        # Verify curated URL is now excluded and delta URL is gone
        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

        curated_url = CuratedUrl.objects.get(url=curated_url.url)
        assert curated_url.excluded is True

        # Remove pattern - this should create new delta URL to show URL will be included
        pattern.delete()

        reversal_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert reversal_delta.excluded is False

        collection.promote_to_curated()
        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

        curated_url = CuratedUrl.objects.get(url=curated_url.url)
        assert curated_url.excluded is False

    def test_promote_and_new_exclude_workflow(self):
        """Test workflow: add URLs, exclude some, promote, then add new exclude pattern."""
        # Initial setup with curated URLs
        [
            CuratedUrlFactory(collection=self.collection, url=f"https://example.com/page{i}", scraped_title=f"Page {i}")
            for i in range(3)
        ]

        # Create first exclude pattern
        DeltaExcludePattern.objects.create(collection=self.collection, match_pattern="https://example.com/page1")

        # Verify delta URL created
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1

        # Simulate promotion
        self.collection.promote_to_curated()

        # Create new exclude pattern after promotion
        pattern2 = DeltaExcludePattern.objects.create(
            collection=self.collection, match_pattern="https://example.com/page2"
        )

        # Should have new delta URL for newly excluded URL
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1
        assert pattern2.delta_urls.count() == 1

    def test_dump_migration_with_excludes(self):
        """Test handling of excluded URLs during dump migration."""
        # Create initial curated URLs
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/test", scraped_title="Original Title"
        )

        # Create exclude pattern, this should not effect the curated
        pattern = DeltaExcludePattern.objects.create(collection=self.collection, match_pattern=curated_url.url)

        # Create dump URL with different content, same as curated, different title, will make delta
        DumpUrlFactory(collection=self.collection, url=curated_url.url, scraped_title="Updated Title")

        # Migrate dump to delta
        self.collection.migrate_dump_to_delta()

        # Should have delta URL reflecting both exclusion and content change
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url is not None
        assert delta_url.scraped_title == "Updated Title"
        assert pattern.delta_urls.filter(id=delta_url.id).exists()
        assert delta_url.excluded is True


class TestDeltaExcludePatternEdgeCases(TestCase):
    """Test edge cases and complex scenarios."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_exclude_pattern_uniqueness(self):
        """Test that we cannot create duplicate exclude patterns for the same URL in a collection."""
        from django.db import transaction

        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/test", scraped_title="Test Title"
        )

        # Create first exclude pattern
        pattern1 = DeltaExcludePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, reason="First exclusion"
        )

        # Verify we start with one pattern
        assert DeltaExcludePattern.objects.filter(collection=self.collection).count() == 1

        # Attempt to create second exclude pattern with same match_pattern should fail
        with pytest.raises(IntegrityError), transaction.atomic():
            DeltaExcludePattern.objects.create(
                collection=self.collection, match_pattern=curated_url.url, reason="Second exclusion"
            )

        # Verify we still only have one pattern
        assert DeltaExcludePattern.objects.filter(collection=self.collection).count() == 1

        # Verify only one delta URL exists and is associated with the pattern
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert pattern1.delta_urls.filter(id=delta_url.id).exists()

    def test_different_patterns_matching_same_url(self):
        """Test that different patterns can affect the same URL."""
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/test/page", scraped_title="Test Title"
        )

        # Create pattern matching exact URL
        pattern1 = DeltaExcludePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, reason="Exact match exclusion"
        )

        # Create pattern with wildcard that also matches the URL
        pattern2 = DeltaExcludePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/test/*",
            match_pattern_type=DeltaExcludePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            reason="Wildcard exclusion",
        )

        # Should still only have one delta URL
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1
        delta_url = DeltaUrl.objects.get(url=curated_url.url)

        # URL should be associated with both patterns
        assert pattern1.delta_urls.filter(id=delta_url.id).exists()
        assert pattern2.delta_urls.filter(id=delta_url.id).exists()

    def test_exclude_modified_url(self):
        """Test excluding a URL that already has modifications in delta doesn't lose delta mods"""
        # Create curated URL
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/test", scraped_title="Original Title"
        )

        # Create modified delta URL
        DeltaUrlFactory(collection=self.collection, url=curated_url.url, scraped_title="Modified Title")

        # Create exclude pattern
        pattern = DeltaExcludePattern.objects.create(collection=self.collection, match_pattern=curated_url.url)

        # Should still only have one delta URL with both modification and exclusion
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1
        updated_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert updated_delta.scraped_title == "Modified Title"
        assert pattern.delta_urls.filter(id=updated_delta.id).exists()

    def test_pattern_update_workflow(self):
        """
        Test updating an exclude pattern's criteria properly updates URL associations
        while preserving existing delta changes.
        """
        # Create multiple curated URLs
        urls = [
            CuratedUrlFactory(
                collection=self.collection, url=f"https://example.com/section{i}/page", scraped_title=f"Page {i}"
            )
            for i in range(3)
        ]

        # Create a delta URL for section1 with a modified title
        DeltaUrlFactory(
            collection=self.collection, url=urls[1].url, scraped_title="Modified Title for Section 1"  # section1
        )

        # Create initial pattern matching section1/*
        pattern = DeltaExcludePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/section1/*",
            match_pattern_type=DeltaExcludePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        # Verify initial state
        assert not pattern.delta_urls.filter(url=urls[0].url).exists()  # section0
        assert pattern.delta_urls.filter(url=urls[1].url).exists()  # section1
        assert not pattern.delta_urls.filter(url=urls[2].url).exists()  # section2

        # Verify the delta URL still exists and has its modified title
        assert DeltaUrl.objects.filter(url=urls[1].url).exists()
        assert DeltaUrl.objects.get(url=urls[1].url).scraped_title == "Modified Title for Section 1"

        # Update pattern to match section2/* instead
        pattern.match_pattern = "https://example.com/section2/*"
        pattern.save()

        # Verify pattern associations have updated correctly
        assert not pattern.delta_urls.filter(url=urls[0].url).exists()  # section0
        assert not pattern.delta_urls.filter(url=urls[1].url).exists()  # section1
        assert pattern.delta_urls.filter(url=urls[2].url).exists()  # section2

        # Verify section1's delta URL still exists with its modified title
        assert DeltaUrl.objects.filter(url=urls[1].url).exists()
        delta_after_update = DeltaUrl.objects.get(url=urls[1].url)
        assert delta_after_update.scraped_title == "Modified Title for Section 1"

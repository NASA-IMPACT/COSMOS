# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_include_patterns.py
import pytest

from sde_collections.models.delta_patterns import (
    DeltaExcludePattern,
    DeltaIncludePattern,
)
from sde_collections.models.delta_url import DeltaUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)


@pytest.mark.django_db
def test_patterns_applied_after_migration():
    collection = CollectionFactory()

    # Add DumpUrls to migrate - using folder-based structure
    DumpUrlFactory(collection=collection, url="https://example.com/excluded_docs/1")
    DumpUrlFactory(collection=collection, url="https://example.com/excluded_docs/2")
    DumpUrlFactory(collection=collection, url="https://example.com/included_docs/1")
    DumpUrlFactory(collection=collection, url="https://example.com/other_docs/1")
    # This URL should be included despite being in excluded_docs folder
    DumpUrlFactory(collection=collection, url="https://example.com/excluded_docs/included")

    # Create exclude pattern for excluded_docs folder
    exclude_pattern = DeltaExcludePattern.objects.create(
        collection=collection, match_pattern="https://example.com/excluded_docs/*", match_pattern_type=2
    )

    # Create include patterns
    include_pattern = DeltaIncludePattern.objects.create(
        collection=collection, match_pattern="https://example.com/included_docs/*", match_pattern_type=2
    )

    # Specific include pattern that overrides the excluded_docs folder
    specific_include = DeltaIncludePattern.objects.create(
        collection=collection, match_pattern="https://example.com/excluded_docs/included", match_pattern_type=1
    )

    # Perform the migration
    collection.migrate_dump_to_delta()

    # Verify pattern relationships
    assert exclude_pattern.delta_urls.filter(
        url="https://example.com/excluded_docs/1"
    ).exists(), "Exclude pattern not applied to excluded_docs"

    assert include_pattern.delta_urls.filter(
        url="https://example.com/included_docs/1"
    ).exists(), "Include pattern not applied to included_docs"

    # Verify URL in other_docs is unaffected
    assert not exclude_pattern.delta_urls.filter(
        url="https://example.com/other_docs/1"
    ).exists(), "Exclude pattern incorrectly applied to other_docs"
    assert not include_pattern.delta_urls.filter(
        url="https://example.com/other_docs/1"
    ).exists(), "Include pattern incorrectly applied to other_docs"

    # Verify excluded status
    excluded_url = DeltaUrl.objects.get(url="https://example.com/excluded_docs/1")
    included_url = DeltaUrl.objects.get(url="https://example.com/included_docs/1")
    neutral_url = DeltaUrl.objects.get(url="https://example.com/other_docs/1")
    override_url = DeltaUrl.objects.get(url="https://example.com/excluded_docs/included")

    assert excluded_url.excluded is True, "URL in excluded_docs should be excluded"
    assert included_url.excluded is False, "URL in included_docs should not be excluded"
    assert neutral_url.excluded is False, "URL in other_docs should not be excluded"
    assert (
        override_url.excluded is False
    ), "Specifically included URL should not be excluded despite being in excluded_docs"

    # Verify both patterns are applied to the override URL
    assert exclude_pattern.delta_urls.filter(url="https://example.com/excluded_docs/included").exists()
    assert specific_include.delta_urls.filter(url="https://example.com/excluded_docs/included").exists()


# Test cases for the updated functionality
@pytest.mark.django_db
class TestUrlExclusionInclusion:
    def test_exclusion_with_no_patterns(self):
        """Test that URLs are not excluded by default"""
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(collection=collection)

        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is False

    def test_exclusion_pattern_only(self):
        """Test that exclude patterns work when no include patterns exist"""
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/excluded")

        DeltaExcludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/excluded", match_pattern_type=1
        )

        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is True

    def test_include_pattern_overrides_exclude(self):
        """Test that include patterns take precedence over exclude patterns"""
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/both")

        # Create both exclude and include patterns for the same URL
        DeltaExcludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/both", match_pattern_type=1
        )

        DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/both", match_pattern_type=1
        )

        # URL should not be excluded because include takes precedence
        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is False

    def test_wildcard_patterns(self):
        """Test that wildcard patterns work correctly with include/exclude precedence"""
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/docs/file.pdf")

        # Exclude all PDFs but include those in /docs/
        DeltaExcludePattern.objects.create(collection=collection, match_pattern="*.pdf", match_pattern_type=2)

        DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/docs/*", match_pattern_type=2
        )

        # URL should not be excluded because the include pattern matches
        assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is False

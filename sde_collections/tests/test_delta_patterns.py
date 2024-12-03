# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_delta_patterns.py

import pytest

from sde_collections.models.delta_patterns import (
    DeltaExcludePattern,
    DeltaResolvedTitleError,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
)
from sde_collections.utils.title_resolver import resolve_title


@pytest.mark.django_db
def test_exclusion_status():
    """
    new patterns should only exclude DeltaUrls, not CuratedUrls
    """
    collection = CollectionFactory()
    curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page/1")
    delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page/2")

    # confirm they both start as not excluded
    assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is False
    assert CuratedUrl.objects.get(pk=curated_url.pk).excluded is False

    # Create an exclusion pattern matches both urls
    pattern = DeltaExcludePattern.objects.create(collection=collection, match_pattern="*page*", match_pattern_type=2)
    pattern.apply()

    # curated urls should not be affected by patterns until the collection is promoted
    # curated should be included, but delta should be excluded
    assert DeltaUrl.objects.get(pk=delta_url.pk).excluded is True
    assert CuratedUrl.objects.get(pk=curated_url.pk).excluded is False


@pytest.mark.django_db
class TestBaseMatchPattern:
    def test_pattern_save_applies_effects(self):
        """Test that pattern creation automatically applies effects."""
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/test")

        # Create pattern - should automatically apply
        pattern = DeltaExcludePattern.objects.create(
            collection=collection, match_pattern=curated_url.url, match_pattern_type=1
        )

        # Delta URL should be created and excluded
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.excluded is True
        assert pattern.delta_urls.filter(id=delta_url.id).exists()

    def test_pattern_delete_removes_effects(self):
        """Test that deleting a pattern properly removes its effects."""
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/test")

        pattern = DeltaExcludePattern.objects.create(collection=collection, match_pattern=curated_url.url)

        # Verify initial state
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.excluded is True

        # Delete pattern
        pattern.delete()

        # Delta URL should be gone since it was only created for exclusion
        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

    def test_different_collections_isolation(self):
        """Test that patterns only affect URLs in their collection."""
        collection1 = CollectionFactory()
        collection2 = CollectionFactory()

        # Create URLs with different paths
        curated_url1 = CuratedUrlFactory(collection=collection1, url="https://example.com/test1")
        curated_url2 = CuratedUrlFactory(collection=collection2, url="https://example.com/test2")

        DeltaExcludePattern.objects.create(
            collection=collection1, match_pattern="https://example.com/*", match_pattern_type=2
        )

        # Only collection1's URL should be affected
        assert DeltaUrl.objects.filter(collection=collection1, url=curated_url1.url).exists()
        assert not DeltaUrl.objects.filter(collection=collection2, url=curated_url2.url).exists()


@pytest.mark.django_db
class TestDeltaTitlePattern:

    def test_apply_generates_delta_url_if_title_differs(self):
        collection = CollectionFactory()
        # Step 1: Create a `CuratedUrl` with a `generated_title` that should differ from the new pattern
        curated_url = CuratedUrlFactory(
            collection=collection,
            url="https://example.com/page",
            scraped_title="Sample Title",
        )

        # Step 2: Create a `DeltaTitlePattern` with a new title pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,  # MULTI_URL_PATTERN
            title_pattern="{title} - Processed New",
        )

        # Step 3: A new DeltaUrl should be created with the updated `generated_title`
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        expected_generated_title = resolve_title(
            pattern.title_pattern,
            {"title": curated_url.scraped_title, "url": curated_url.url, "collection": collection.name},
        )
        assert delta_url.generated_title == expected_generated_title

    def test_apply_does_not_generate_delta_url_if_titles_match(self):
        collection = CollectionFactory()
        title_pattern = "{title} - Processed"
        context = {
            "url": "https://example.com/page",
            "title": "Sample Title",
            "collection": collection.name,
        }
        curated_url = CuratedUrlFactory(
            collection=collection,
            url=context["url"],
            scraped_title=context["title"],
            generated_title=resolve_title(title_pattern, context),
        )

        # Create and apply a `DeltaTitlePattern` with the same title pattern
        DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern=title_pattern,
        )
        # pattern.apply()

        # Since the title matches, no new `DeltaUrl` should be created
        DeltaUrl.objects.filter(url=curated_url.url).first()

        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

    def test_apply_resolves_title_for_delta_urls(self):
        collection = CollectionFactory()
        # Create a `DeltaUrl` that will be matched and have the title pattern applied
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="Sample Title")

        # Create and apply a `DeltaTitlePattern` to apply a generated title
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern="{title} - Processed",
        )
        pattern.apply()

        # The `generated_title` in `DeltaUrl` should reflect the applied pattern
        delta_url.refresh_from_db()
        expected_generated_title = resolve_title(pattern.title_pattern, {"title": delta_url.scraped_title})
        assert delta_url.generated_title == expected_generated_title

    def test_apply_logs_error_on_title_resolution_failure(self):
        # TODO: note that if you apply a pattern with an error multiple times
        # it will not log multiple errors on a url. it will instead throw a duplicate key error
        # at some point, the error code should be made more robust to handle this
        collection = CollectionFactory()
        # Create a `DeltaUrl` that will trigger a resolution error
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="Sample Title")

        # Create a `DeltaTitlePattern` with an invalid title pattern to trigger an error
        DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern="{invalid_field} - Processed",
        )

        # Check that a `DeltaResolvedTitleError` was logged
        error_entry = DeltaResolvedTitleError.objects.get(delta_url__url=delta_url.url)
        assert "invalid_field" in error_entry.error_string

    def test_unapply_clears_generated_titles_from_delta_urls(self):
        collection = CollectionFactory()
        # Create a `DeltaUrl` with an existing `scraped_title`
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="Sample Title")

        # Create and apply a `DeltaTitlePattern`
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern="{title} - Processed",
        )
        delta_url.refresh_from_db()
        assert delta_url.generated_title == "Sample Title - Processed"

        # Unapply the pattern, which should clear the `generated_title` in `DeltaUrl`
        pattern.delete()
        delta_url.refresh_from_db()
        assert delta_url.generated_title == ""

    def test_unapply_removes_pattern_relationships(self):
        collection = CollectionFactory()
        # Create a `CuratedUrl` and matching `DeltaUrl`
        curated_url = CuratedUrlFactory(
            collection=collection, url="https://example.com/page", scraped_title="Sample Title"
        )
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="New Title")

        # Create and apply a `DeltaTitlePattern`
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern="{title} - Processed",
        )
        pattern.apply()
        pattern.refresh_from_db()

        # Ensure relationships are set
        assert pattern.delta_urls.filter(pk=delta_url.pk).exists()
        # this actually shouldn't match until after promotion
        assert not pattern.curated_urls.filter(pk=curated_url.pk).exists()

        # Unapply the pattern
        pattern.unapply()

        # Verify relationships have been cleared
        assert not pattern.delta_urls.filter(pk=delta_url.pk).exists()
        assert not pattern.curated_urls.filter(pk=curated_url.pk).exists()

    def test_pattern_reapplication_does_not_duplicate_delta_urls(self):
        """
        Ensures that reapplying a pattern does not create duplicate `DeltaUrls` or affect existing `CuratedUrls`.
        """
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="Title Before")

        # Apply a pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,
            title_pattern="{title} - Processed",
        )

        delta_url.refresh_from_db()
        delta_url.generated_title = "Title Before - Processed"

        # Promote to CuratedUrl
        collection.promote_to_curated()
        curated_url = CuratedUrl.objects.get(url=delta_url.url)

        # Ensure no new `DeltaUrl` is created after reapplying the pattern
        pattern.apply()
        assert DeltaUrl.objects.filter(url=curated_url.url).count() == 0

        # Ensure no new `DeltaUrl` is created after reapplying the pattern
        pattern.apply()
        assert DeltaUrl.objects.filter(url=curated_url.url).count() == 0

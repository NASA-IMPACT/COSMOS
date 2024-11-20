# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_delta_patterns.py

import pytest

from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import (
    CuratedUrl,
    DeltaResolvedTitleError,
    DeltaUrl,
)
from sde_collections.tests.factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)
from sde_collections.utils.title_resolver import resolve_title


@pytest.mark.django_db
def test_exclusion_status():
    collection = CollectionFactory()
    curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")

    # Create an exclusion pattern that should apply to this URL
    DeltaExcludePattern.objects.create(collection=collection, match_pattern="https://example.com/page")

    # Assert that the `excluded` field is set to True, as expected
    assert CuratedUrl.objects.get(pk=curated_url.pk).excluded


@pytest.mark.django_db
class TestBaseMatchPattern:
    def test_individual_url_pattern_matching(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")
        pattern = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/page", match_pattern_type=1  # INDIVIDUAL_URL
        )
        pattern.apply()
        matching_urls = pattern.matched_urls()
        CuratedUrl.objects.filter(collection=collection, url__regex=pattern.match_pattern)

        assert curated_url in matching_urls["matching_curated_urls"]

    def test_multi_url_pattern_matching(self):
        collection = CollectionFactory()
        curated_url_1 = CuratedUrlFactory(collection=collection, url="https://example.com/page1")
        curated_url_2 = CuratedUrlFactory(collection=collection, url="https://example.com/page2")
        pattern = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2  # MULTI_URL_PATTERN
        )

        matching_urls = pattern.matched_urls()
        assert curated_url_1 in matching_urls["matching_curated_urls"]
        assert curated_url_2 in matching_urls["matching_curated_urls"]

    def test_generate_delta_url_creation_and_update(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")
        pattern = DeltaIncludePattern.objects.create(collection=collection, match_pattern="https://example.com/page")

        # First call to generate DeltaUrl
        pattern.generate_delta_url(curated_url, fields_to_copy=["scraped_title"])
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        original_delta_title = delta_url.scraped_title
        assert delta_url.scraped_title == curated_url.scraped_title

        # Update DeltaUrl with additional fields
        # this is kinda weird, but basically if you have a deltaurl with a
        # scraped_title, that value is gospel. if for some reason generate_delta_url is called
        # again and it hits that deltaurl, it will not update the scraped_title field, since that
        # field already exists and is assumed correct.
        # this is true of title. but i think not of other fields?
        curated_url.scraped_title = "Updated Title"
        curated_url.save()
        curated_url.refresh_from_db()
        pattern.generate_delta_url(curated_url, fields_to_copy=["scraped_title"])
        delta_url.refresh_from_db()
        assert delta_url.scraped_title == original_delta_title

    def test_apply_creates_delta_url_if_curated_url_does_not_exist(self):
        """
        Ensures that the `apply` logic creates a new `DeltaUrl` if a matching `CuratedUrl` does not exist.
        """
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(
            collection=collection, url="https://example.com/page", scraped_title="Original Title"
        )

        # Create a pattern matching the URL
        pattern = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2
        )

        # Apply the pattern
        pattern.apply()

        # Verify that a DeltaUrl is created
        assert DeltaUrl.objects.filter(url=delta_url.url).exists()

    def test_apply_skips_delta_url_creation_if_curated_url_exists(self):
        """
        Ensures that the `apply` logic does not create a new `DeltaUrl` if a matching `CuratedUrl` already exists.
        """
        collection = CollectionFactory()
        delta_url = DeltaUrlFactory(
            collection=collection, url="https://example.com/page", scraped_title="Original Title"
        )

        # Create a pattern matching the URL
        pattern = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2
        )

        # Promote the DeltaUrl to a CuratedUrl
        collection.promote_to_curated()
        curated_url = CuratedUrl.objects.get(url=delta_url.url)

        # ReApply the pattern
        pattern.apply()

        # Verify that no DeltaUrl is created after the CuratedUrl exists
        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

    def test_apply_creates_delta_url_if_no_curated_url_exists(self):
        """
        Ensures that if no `CuratedUrl` exists for a given pattern, a new `DeltaUrl` is created.
        """
        collection = CollectionFactory()
        dump_url = DumpUrlFactory(collection=collection, url="https://example.com/page", scraped_title="New Title")

        # Migrate DumpUrl to DeltaUrl
        collection.migrate_dump_to_delta()

        # Create a pattern matching the URL
        pattern = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2
        )

        # Apply the pattern
        pattern.apply()

        # A `DeltaUrl` should now exist
        delta_url = DeltaUrl.objects.get(url=dump_url.url)
        assert delta_url.scraped_title == dump_url.scraped_title

    def test_apply_and_unapply_pattern(self):
        # if we make a new exclude pattern and it affects an old url
        # that wasn't previously affected, what should happen?
        # for now, let's say the curated_url should be excluded, and a delta_url is created which is also excluded
        # when the pattern is deleted, they should both be unexcluded again
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")
        assert not CuratedUrl.objects.get(pk=curated_url.pk).excluded

        pattern = DeltaExcludePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,  # MULTI_URL_PATTERN
        )

        assert CuratedUrl.objects.get(pk=curated_url.pk).excluded
        assert DeltaUrl.objects.get(url=curated_url.url).excluded

        pattern.delete()

        # TODO: for now the DeltaUrl is persisting, but i think we might want to find a way to delete it eventually
        assert not CuratedUrl.objects.get(pk=curated_url.pk).excluded
        assert not DeltaUrl.objects.get(url=curated_url.url).excluded


@pytest.mark.django_db
class TestDeltaTitlePattern:

    def test_apply_generates_delta_url_if_title_differs(self):
        collection = CollectionFactory()
        # Step 1: Create a `CuratedUrl` with a `generated_title` that should differ from the new pattern
        curated_url = CuratedUrlFactory(
            collection=collection,
            url="https://example.com/page",
            scraped_title="Sample Title",
            generated_title="Old Title - Processed",
        )

        # Step 2: Create a `DeltaTitlePattern` with a new title pattern
        pattern = DeltaTitlePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/*",
            match_pattern_type=2,  # MULTI_URL_PATTERN
            title_pattern="{title} - Processed New",
        )

        # Apply the pattern
        pattern.apply()

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
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com/page", scraped_title="Sample Title")

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
        assert pattern.curated_urls.filter(pk=curated_url.pk).exists()

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


@pytest.mark.django_db
class TestDeltaDocumentTypePattern:
    def test_apply_document_type_pattern(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")
        pattern = DeltaDocumentTypePattern.objects.create(
            collection=collection,
            match_pattern="https://example.com/page",
            document_type=2,  # A different document type than default
        )
        pattern.apply()

        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.document_type == 2

    def test_unapply_document_type_pattern(self):
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page")
        pattern = DeltaDocumentTypePattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2, document_type=2
        )
        pattern.apply()

        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.document_type == 2

        pattern.unapply()
        delta_url.refresh_from_db()
        assert delta_url.document_type is None


@pytest.mark.django_db
class TestDeltaDivisionPattern:
    def test_apply_and_unapply_division_pattern(self):
        # Step 1: Create a collection and a CuratedUrl that matches the pattern
        collection = CollectionFactory()
        curated_url = CuratedUrlFactory(collection=collection, url="https://example.com/page", division=1)

        # Step 2: Create a DeltaDivisionPattern to apply to matching URLs
        pattern = DeltaDivisionPattern.objects.create(
            collection=collection, match_pattern="https://example.com/*", match_pattern_type=2, division=2
        )

        # Step 3: Apply the pattern, which should generate a DeltaUrl with the division set to 2
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.division == 2

        # confirm the curated url maintains its original division
        curated_url = CuratedUrl.objects.get(url=curated_url.url)
        assert curated_url.division == 1

        # Step 4: Unapply the pattern and confirm the division field is cleared
        pattern.unapply()
        delta_url.refresh_from_db()
        assert delta_url.division is None

# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_pattern_specificity.py

import pytest

from sde_collections.models.collection_choice_fields import DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDocumentTypePattern,
    DeltaResolvedTitle,
    DeltaTitlePattern,
)
from sde_collections.models.delta_url import DeltaUrl
from sde_collections.tests.factories import CollectionFactory, DeltaUrlFactory


@pytest.mark.django_db
def test_title_pattern_multiple_resolved_titles_extended():
    """Test that patterns properly handle title resolution based on URL set size."""
    collection = CollectionFactory()

    # Create URLs with different levels of specificity
    url1 = DeltaUrlFactory(
        collection=collection, url="https://example.com/docs/item.html", scraped_title="Original Title"
    )
    url2 = DeltaUrlFactory(
        collection=collection, url="https://example.com/docs/item2.html", scraped_title="Original Title"
    )
    url3 = DeltaUrlFactory(
        collection=collection, url="https://example.com/docs/pdfs/item1.html", scraped_title="Original Title"
    )

    # Create general pattern (matches all URLs)
    general_pattern = DeltaTitlePattern.objects.create(
        collection=collection,
        match_pattern="*docs*",
        title_pattern="{title} - Docs",
        match_pattern_type=2,
    )

    # Verify initial pattern application
    assert general_pattern.get_url_match_count() == 3
    assert DeltaUrl.objects.get(pk=url1.pk).generated_title == "Original Title - Docs"
    assert DeltaUrl.objects.get(pk=url2.pk).generated_title == "Original Title - Docs"
    assert DeltaUrl.objects.get(pk=url3.pk).generated_title == "Original Title - Docs"

    # Verify DeltaResolvedTitle entries
    assert DeltaResolvedTitle.objects.count() == 3
    for url in [url1, url2, url3]:
        resolved = DeltaResolvedTitle.objects.get(delta_url=url)
        assert resolved.title_pattern == general_pattern
        assert resolved.resolved_title == "Original Title - Docs"

    # Create more specific pattern
    specific_pattern = DeltaTitlePattern.objects.create(
        collection=collection, match_pattern="*docs/pdfs*", title_pattern="{title} - HTML", match_pattern_type=2
    )

    # Verify pattern match counts
    assert specific_pattern.get_url_match_count() == 1  # Only matches pdfs URL
    assert general_pattern.get_url_match_count() == 3  # Matches all URLs

    # Verify titles were updated appropriately
    assert DeltaUrl.objects.get(pk=url1.pk).generated_title == "Original Title - Docs"  # Unchanged
    assert DeltaUrl.objects.get(pk=url2.pk).generated_title == "Original Title - Docs"  # Unchanged
    assert DeltaUrl.objects.get(pk=url3.pk).generated_title == "Original Title - HTML"  # Updated

    # Verify DeltaResolvedTitle entries
    assert DeltaResolvedTitle.objects.count() == 3  # Still one per URL

    # URLs with general pattern should be unchanged
    for url in [url1, url2]:
        resolved = DeltaResolvedTitle.objects.get(delta_url=url)
        assert resolved.title_pattern == general_pattern
        assert resolved.resolved_title == "Original Title - Docs"

    # PDF URL should now use specific pattern
    resolved_pdf = DeltaResolvedTitle.objects.get(delta_url=url3)
    assert resolved_pdf.title_pattern == specific_pattern
    assert resolved_pdf.resolved_title == "Original Title - HTML"

    # Verify pattern relationships are maintained
    assert url1 in general_pattern.delta_urls.all()
    assert url2 in general_pattern.delta_urls.all()
    assert url3 in general_pattern.delta_urls.all()
    assert url3 in specific_pattern.delta_urls.all()


@pytest.mark.django_db
def test_field_modifying_pattern_layered_specificity():
    """Test overlapping patterns with different levels of specificity."""
    collection = CollectionFactory()

    # Create URLs in a hierarchy that allows for overlapping pattern matches
    deep_tool = DeltaUrlFactory(
        collection=collection,
        url="https://example.com/tools/analysis/v2/processor.py",
        document_type=DocumentTypes.DOCUMENTATION,  # Starting as documentation
    )
    mid_tool = DeltaUrlFactory(
        collection=collection,
        url="https://example.com/tools/analysis/helper.py",
        document_type=DocumentTypes.DOCUMENTATION,  # Starting as documentation
    )
    top_tool = DeltaUrlFactory(
        collection=collection,
        url="https://example.com/tools/simple.py",
        document_type=DocumentTypes.DOCUMENTATION,  # Starting as documentation
    )

    # Create patterns with overlapping matches
    broad_pattern = DeltaDocumentTypePattern.objects.create(
        collection=collection,
        match_pattern="*/tools/*.py",  # Matches all 3 URLs
        document_type=DocumentTypes.SOFTWARETOOLS,
        match_pattern_type=2,
    )

    mid_pattern = DeltaDocumentTypePattern.objects.create(
        collection=collection,
        match_pattern="*/tools/analysis/*.py",  # Matches 2 URLs (mid and deep)
        document_type=DocumentTypes.DATA,  # Different type to clearly show which pattern won
        match_pattern_type=2,
    )

    specific_pattern = DeltaDocumentTypePattern.objects.create(
        collection=collection,
        match_pattern="*/analysis/v2/*.py",  # Matches only 1 URL (deep)
        document_type=DocumentTypes.DOCUMENTATION,  # Different type to clearly show which pattern won
        match_pattern_type=2,
    )

    # Verify URL match counts
    assert broad_pattern.get_url_match_count() == 3
    assert mid_pattern.get_url_match_count() == 2
    assert specific_pattern.get_url_match_count() == 1

    # Verify patterns were applied correctly based on specificity
    deep_tool.refresh_from_db()
    mid_tool.refresh_from_db()
    top_tool.refresh_from_db()

    # The most specific pattern (1 match) should win for the deep URL
    assert deep_tool.document_type == DocumentTypes.DOCUMENTATION, "Deep URL should use most specific pattern"

    # The mid-level pattern (2 matches) should win for the middle URL
    assert mid_tool.document_type == DocumentTypes.DATA, "Mid URL should use mid-level pattern"

    # The broad pattern (3 matches) should only affect the top URL
    assert top_tool.document_type == DocumentTypes.SOFTWARETOOLS, "Top URL should use broad pattern"

    # Verify the relationships are tracked correctly
    assert deep_tool.pk in specific_pattern.delta_urls.values_list("pk", flat=True)
    assert deep_tool.pk in mid_pattern.delta_urls.values_list("pk", flat=True)
    assert deep_tool.pk in broad_pattern.delta_urls.values_list("pk", flat=True)

    assert mid_tool.pk in mid_pattern.delta_urls.values_list("pk", flat=True)
    assert mid_tool.pk in broad_pattern.delta_urls.values_list("pk", flat=True)

    assert top_tool.pk in broad_pattern.delta_urls.values_list("pk", flat=True)

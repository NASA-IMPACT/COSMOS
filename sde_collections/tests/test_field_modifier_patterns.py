# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_field_modifier_patterns.py

import pytest
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.test import TestCase

from sde_collections.models.collection_choice_fields import Divisions, DocumentTypes
from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
)
from sde_collections.models.delta_url import CuratedUrl, DeltaUrl

from .factories import CollectionFactory, CuratedUrlFactory, DeltaUrlFactory


class BaseCollectionTest(TestCase):
    def setUp(self):
        super().setUp()
        self.collection = CollectionFactory()

        # Ensure ContentTypes are created for all pattern models
        for model in [
            "deltaexcludepattern",
            "deltaincludepattern",
            "deltatitlepattern",
            "deltadocumenttypepattern",
            "deltadivisionpattern",
        ]:
            ContentType.objects.get_or_create(
                app_label="sde_collections",
                model=model,
            )


@pytest.mark.django_db
class TestFieldModifierPatternBasics(TestCase):
    """Test basic functionality of field modifier patterns."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_create_document_type_pattern_single(self):
        """Test creation of a document type pattern for single URL."""
        pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/guide.pdf",
            document_type=DocumentTypes.DOCUMENTATION,
        )
        assert pattern.match_pattern_type == DeltaDocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL
        assert pattern.document_type == DocumentTypes.DOCUMENTATION

    def test_create_document_type_pattern_multi(self):
        """Test creation of a document type pattern with wildcard."""
        pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/docs/*.pdf",
            match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
            document_type=DocumentTypes.DOCUMENTATION,
        )
        assert pattern.match_pattern_type == DeltaDocumentTypePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN
        assert pattern.document_type == DocumentTypes.DOCUMENTATION

    def test_create_division_pattern(self):
        """Test creation of a division pattern."""
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/helio/data.html",
            division=Divisions.HELIOPHYSICS,
        )
        assert pattern.match_pattern_type == DeltaDivisionPattern.MatchPatternTypeChoices.INDIVIDUAL_URL
        assert pattern.division == Divisions.HELIOPHYSICS

    def test_modify_single_curated_url_document_type(self):
        """Test modifying document type for a single curated URL."""
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/tools/analysis.html", document_type=DocumentTypes.DATA
        )

        pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, document_type=DocumentTypes.SOFTWARETOOLS
        )

        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url is not None
        assert delta_url.document_type == DocumentTypes.SOFTWARETOOLS
        assert pattern.delta_urls.filter(id=delta_url.id).exists()
        # curated url should be unchanged
        assert CuratedUrl.objects.get(url=curated_url.url).document_type == DocumentTypes.DATA

    def test_modify_single_curated_url_division(self):
        """Test modifying division for a single curated URL."""
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/planetary/mars.html", division=Divisions.EARTH_SCIENCE
        )

        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.PLANETARY
        )

        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url is not None
        assert delta_url.division == Divisions.PLANETARY
        assert pattern.delta_urls.filter(id=delta_url.id).exists()


@pytest.mark.django_db
class TestFieldModifierPatternBehavior(TestCase):
    """Test complex behaviors of field modifier patterns."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_pattern_with_existing_delta(self):
        """Test applying pattern when delta URL already exists."""
        curated_url = CuratedUrlFactory(
            collection=self.collection,
            url="https://example.com/instruments/telescope.html",
            document_type=DocumentTypes.DOCUMENTATION,
        )

        # Create delta URL with different title
        delta_url = DeltaUrlFactory(
            collection=self.collection,
            url=curated_url.url,
            scraped_title="Updated Telescope Info",
            document_type=DocumentTypes.DOCUMENTATION,
        )

        # Apply pattern - should modify existing delta
        DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, document_type=DocumentTypes.MISSIONSINSTRUMENTS
        )

        # Should still be only one delta URL with both changes
        assert DeltaUrl.objects.filter(collection=self.collection).count() == 1
        updated_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert updated_delta.id == delta_url.id
        assert updated_delta.document_type == DocumentTypes.MISSIONSINSTRUMENTS
        assert updated_delta.scraped_title == "Updated Telescope Info"
        assert CuratedUrl.objects.get(url=curated_url.url).document_type == DocumentTypes.DOCUMENTATION

    def test_multi_url_pattern_modification(self):
        """Test modifying multiple URLs with wildcard pattern."""
        # Create multiple curated URLs
        [
            CuratedUrlFactory(
                collection=self.collection,
                url=f"https://example.com/images/galaxy{i}.jpg",
                document_type=DocumentTypes.DOCUMENTATION,
            )
            for i in range(3)
        ]

        pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/images/*.jpg",
            document_type=DocumentTypes.IMAGES,
            match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        assert DeltaUrl.objects.filter(collection=self.collection).count() == 3
        for delta_url in DeltaUrl.objects.all():
            assert delta_url.document_type == DocumentTypes.IMAGES
            assert pattern.delta_urls.filter(id=delta_url.id).exists()


@pytest.mark.django_db
class TestFieldModifierPatternLifecycle(TestCase):
    """Test pattern lifecycle including promotion and removal."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_pattern_removal_creates_reversal_deltas(self):
        """Test that removing a pattern creates deltas to reverse its effects."""
        curated_url = CuratedUrlFactory(
            collection=self.collection, url="https://example.com/bio/experiment.html", division=Divisions.GENERAL
        )

        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.BIOLOGY
        )

        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.division == Divisions.BIOLOGY

        self.collection.promote_to_curated()

        curated_url = CuratedUrl.objects.get(url=curated_url.url)

        assert curated_url.division == Divisions.BIOLOGY
        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

        pattern.delete()

        # when all you have in the system is a curated url and a pattern setting a value
        # removal of the pattern should make a delta that sets the value to None
        reversal_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert reversal_delta.division is None

    def test_multiple_patterns_same_url(self):
        """Test that different types of patterns can affect same URL."""
        url = "https://example.com/astro/telescope_data.fits"

        CuratedUrlFactory(
            collection=self.collection, url=url, division=Divisions.GENERAL, document_type=DocumentTypes.DOCUMENTATION
        )

        # Apply both division and document type patterns
        division_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=url, division=Divisions.ASTROPHYSICS
        )

        doc_type_pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=url, document_type=DocumentTypes.DATA
        )

        # Should have one delta URL reflecting both changes
        assert DeltaUrl.objects.count() == 1
        delta_url = DeltaUrl.objects.get()
        assert delta_url.division == Divisions.ASTROPHYSICS
        assert delta_url.document_type == DocumentTypes.DATA
        assert division_pattern.delta_urls.filter(id=delta_url.id).exists()
        assert doc_type_pattern.delta_urls.filter(id=delta_url.id).exists()


@pytest.mark.django_db
class TestFieldModifierPatternConstraints(TestCase):
    """Test pattern constraints and validation."""

    def setUp(self):
        self.collection = CollectionFactory()

    def test_pattern_uniqueness_per_collection(self):
        """Test that patterns must be unique per collection."""
        url = "https://example.com/data/sample.fits"

        DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=url, document_type=DocumentTypes.DATA
        )

        with pytest.raises(IntegrityError):
            DeltaDocumentTypePattern.objects.create(
                collection=self.collection, match_pattern=url, document_type=DocumentTypes.DOCUMENTATION
            )


@pytest.mark.django_db
class TestFieldModifierDeltaCleanup(TestCase):
    """
    Test complex delta URL cleanup scenarios, particularly around pattern removal
    and interaction between multiple patterns.
    """

    def setUp(self):
        self.collection = CollectionFactory()

    def test_delta_retained_with_other_changes(self):
        """
        Test that a delta URL with changes from multiple patterns is properly
        handled when one pattern is removed.
        """
        curated_url = CuratedUrlFactory(
            collection=self.collection,
            url="https://example.com/astro/data.fits",
            division=Divisions.GENERAL,
            document_type=DocumentTypes.DOCUMENTATION,
            scraped_title="Original Title",  # Adding this to test preservation of manual changes
        )

        # Create two patterns affecting the same URL
        division_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.ASTROPHYSICS
        )

        DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, document_type=DocumentTypes.DATA
        )

        # Manually modify the title to simulate a non-pattern change
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        delta_url.scraped_title = "Modified Title"
        delta_url.save()

        # Remove one pattern - delta should be retained with other changes
        division_pattern.delete()

        # Delta should still exist with doc type change and manual title change
        retained_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert retained_delta.document_type == DocumentTypes.DATA
        assert retained_delta.scraped_title == "Modified Title"
        assert retained_delta.division == Divisions.GENERAL  # Division reverted to curated value

    def test_delta_cleanup_after_all_patterns_removed(self):
        """
        Test cleanup of delta URLs when all patterns affecting them are removed,
        but only if no other changes exist.
        """
        curated_url = CuratedUrlFactory(
            collection=self.collection,
            url="https://example.com/astro/data.fits",
            division=Divisions.GENERAL,
            document_type=DocumentTypes.DOCUMENTATION,
        )

        doc_type_pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, document_type=DocumentTypes.DATA
        )

        # Verify delta exists with both changes
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        assert delta_url.document_type == DocumentTypes.DATA

        # Remove pattern
        doc_type_pattern.delete()

        assert not DeltaUrl.objects.filter(url=curated_url.url).exists()

    def test_delta_cleanup_with_manual_changes(self):
        """
        Test that deltas are retained when patterns are removed but manual changes exist.
        """
        curated_url = CuratedUrlFactory(
            collection=self.collection,
            url="https://example.com/astro/data.fits",
            division=Divisions.GENERAL,
            document_type=DocumentTypes.DOCUMENTATION,
            scraped_title="Original Title",
        )

        # Create pattern and let it create a delta
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.ASTROPHYSICS
        )

        # Add manual change to delta
        delta_url = DeltaUrl.objects.get(url=curated_url.url)
        delta_url.scraped_title = "Modified Title"
        delta_url.save()

        # Remove pattern
        pattern.delete()

        # Delta should be retained due to manual title change
        retained_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert retained_delta.scraped_title == "Modified Title"
        assert retained_delta.division == Divisions.GENERAL

    def test_multi_url_pattern_cleanup(self):
        """
        Test cleanup behavior when removing a pattern that affects multiple URLs.
        """
        # Create several curated URLs
        curated_urls = [
            CuratedUrlFactory(
                collection=self.collection,
                url=f"https://example.com/data/set{i}.fits",
                document_type=DocumentTypes.DOCUMENTATION,
            )
            for i in range(3)
        ]

        # Create pattern affecting all URLs
        pattern = DeltaDocumentTypePattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/data/*.fits",
            document_type=DocumentTypes.DATA,
            match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        # Modify one delta with additional changes
        delta_to_retain = DeltaUrl.objects.get(url=curated_urls[0].url)
        delta_to_retain.scraped_title = "Modified Title"
        delta_to_retain.save()

        # Remove pattern
        pattern.delete()

        # Only the delta with manual changes should remain
        assert DeltaUrl.objects.count() == 1
        retained_delta = DeltaUrl.objects.get()
        assert retained_delta.url == curated_urls[0].url
        assert retained_delta.scraped_title == "Modified Title"
        assert retained_delta.document_type == DocumentTypes.DOCUMENTATION

    def test_pattern_removal_after_promotion(self):
        """
        Test that removing a pattern after promotion creates appropriate reversal deltas.
        """
        curated_urls = [
            CuratedUrlFactory(
                collection=self.collection,
                url=f"https://example.com/helio/data{i}.fits",
                division=Divisions.GENERAL,
                document_type=DocumentTypes.DOCUMENTATION,
            )
            for i in range(2)
        ]

        # Create patterns and manually modify one URL
        division_pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection,
            match_pattern="https://example.com/helio/*.fits",
            division=Divisions.HELIOPHYSICS,
            match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
        )

        # Modify first delta with additional changes
        delta = DeltaUrl.objects.get(url=curated_urls[0].url)
        delta.scraped_title = "Modified Title"
        delta.save()

        # Promote collection
        self.collection.promote_to_curated()

        # Remove pattern - should create reversal deltas
        division_pattern.delete()

        # Should have two deltas: one with just division reversal,
        # one with division reversal plus preserved title change
        assert DeltaUrl.objects.count() == 2

        # Check delta with manual changes
        modified_delta = DeltaUrl.objects.get(url=curated_urls[0].url)
        assert modified_delta.division is None
        assert modified_delta.scraped_title == "Modified Title"

        # Check plain reversal delta
        plain_delta = DeltaUrl.objects.get(url=curated_urls[1].url)
        assert plain_delta.division is None
        assert plain_delta.scraped_title == curated_urls[1].scraped_title

    def test_pattern_removal_creates_null_deltas(self):
        """ """
        curated_url = DeltaUrlFactory(
            collection=self.collection,
            url="https://example.com/astro/data.fits",
            division=Divisions.ASTROPHYSICS,
            document_type=DocumentTypes.DATA,
        )

        # Create pattern
        pattern = DeltaDivisionPattern.objects.create(
            collection=self.collection, match_pattern=curated_url.url, division=Divisions.HELIOPHYSICS
        )

        # Verify initial state
        delta = DeltaUrl.objects.get(url=curated_url.url)
        assert delta.division == Divisions.HELIOPHYSICS

        # Remove pattern
        pattern.delete()

        # Should have delta with explicit NULL
        new_delta = DeltaUrl.objects.get(url=curated_url.url)
        assert new_delta.division is None

    # def test_pattern_removal_with_multiple_patterns(self):
    #     """
    #     Test that removing one pattern doesn't NULL the field if other
    #     patterns of same type still affect the URL.
    #     """
    #     # TODO: The official stance right now is to simply not make overlapping patterns like this
    #     # in the future, if this behavior is allowed, then this would be the test case.
    #     # right now, this behavior is not coded for, and this test does not pass.

    #     curated_url = CuratedUrlFactory(
    #         collection=self.collection, url="https://example.com/astro/data.fits", division=Divisions.GENERAL
    #     )

    #     # Create two patterns affecting same URL
    #     pattern1 = DeltaDivisionPattern.objects.create(
    #         collection=self.collection,
    #         match_pattern="*.fits",
    #         division=Divisions.ASTROPHYSICS,
    #         match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN,
    #     )

    #     DeltaDivisionPattern.objects.create(
    #         collection=self.collection, match_pattern=curated_url.url, division=Divisions.HELIOPHYSICS
    #     )

    #     # Remove one pattern
    #     pattern1.delete()

    #     # Delta should retain value from remaining pattern
    #     delta = DeltaUrl.objects.get(url=curated_url.url)
    #     assert delta.division == Divisions.HELIOPHYSICS

# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/test_tdamm_tags.py

import pytest

from sde_collections.tests.factories import (
    CollectionFactory,
    DeltaUrlFactory,
    DumpUrlFactory,
)

from ..models.delta_url import CuratedUrl, DeltaUrl


@pytest.mark.django_db
class TestTDAMMFields:
    """Test core TDAMM tags functionality with DeltaUrl"""

    def test_manual_and_ml_field_behavior(self):
        """Test the relationship between manual and ML fields"""
        url = DeltaUrlFactory()

        # Setting tdamm_tag affects only manual field
        url.tdamm_tag = ["MMA_M_EM", "MMA_M_G"]
        assert url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G"]
        assert url.tdamm_tag_ml is None

        # ML field must be set explicitly
        url.tdamm_tag_ml = ["MMA_M_N"]
        assert url.tdamm_tag_ml == ["MMA_M_N"]
        assert url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G"]

    def test_field_priority(self):
        """Test that manual field takes priority over ML field"""
        url = DeltaUrlFactory()

        # Set ML tags first
        url.tdamm_tag_ml = ["MMA_M_EM"]
        assert url.tdamm_tag == ["MMA_M_EM"]

        # Set manual tags - should take priority
        url.tdamm_tag = ["MMA_M_G"]
        assert url.tdamm_tag == ["MMA_M_G"]

        # Clear manual tags - should fall back to ML tags
        url.tdamm_tag_manual = None
        assert url.tdamm_tag == ["MMA_M_EM"]

    def test_empty_array_behavior(self):
        """Test handling of empty arrays vs None"""
        url = DeltaUrlFactory()

        # Set ML tags
        url.tdamm_tag_ml = ["MMA_M_EM"]
        assert url.tdamm_tag == ["MMA_M_EM"]

        # Empty manual array should not override ML tags
        url.tdamm_tag = []
        assert url.tdamm_tag == ["MMA_M_EM"]

        # None manual value should not override ML tags
        url.tdamm_tag = None
        assert url.tdamm_tag == ["MMA_M_EM"]

    def test_field_deletion(self):
        """Test deletion of fields"""
        url = DeltaUrlFactory()

        # Set both manual and ML tags
        url.tdamm_tag = ["MMA_M_EM"]
        url.tdamm_tag_ml = ["MMA_M_G"]

        # Delete tdamm_tag
        del url.tdamm_tag
        assert url.tdamm_tag_manual is None
        assert url.tdamm_tag_ml is None

    def test_multiple_tags(self):
        """Test handling of multiple tags"""
        url = DeltaUrlFactory()

        # Test multiple manual tags
        manual_tags = ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        url.tdamm_tag = manual_tags
        assert url.tdamm_tag_manual == manual_tags

        # Test multiple ML tags
        ml_tags = ["MMA_O_BH", "MMA_O_N"]
        url.tdamm_tag_ml = ml_tags
        assert url.tdamm_tag_ml == ml_tags

    def test_persistence(self):
        """Test that values persist after save"""
        url = DeltaUrlFactory()

        # Set values
        url.tdamm_tag = ["MMA_M_EM"]
        url.tdamm_tag_ml = ["MMA_M_G"]
        url.save()

        # Refresh from database
        url.refresh_from_db()
        assert url.tdamm_tag_manual == ["MMA_M_EM"]
        assert url.tdamm_tag_ml == ["MMA_M_G"]


@pytest.mark.django_db
class TestTDAMMTagMigration:
    """Test TDAMM tag behavior during the migration process"""

    @pytest.fixture
    def collection(self):
        return CollectionFactory()

    def test_tdamm_tags_preserved_in_migration(self, collection):
        """Test that TDAMM tags are preserved when promoting from Dump to Delta"""
        dump_url = DumpUrlFactory(collection=collection, url="https://example.com")
        dump_url.tdamm_tag = ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        dump_url.tdamm_tag_ml = ["MMA_O_BH", "MMA_O_N"]
        dump_url.save()

        # Migrate to delta
        collection.migrate_dump_to_delta()

        # Verify tags in the migrated DeltaUrl
        delta_url = DeltaUrl.objects.get(url="https://example.com")
        assert delta_url.tdamm_tag == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert delta_url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert delta_url.tdamm_tag_ml == ["MMA_O_BH", "MMA_O_N"]

    def test_tdamm_tags_updated_in_migration(self, collection):
        """Test that TDAMM tags are updated during re-migration"""
        # Initial migration
        dump_url = DumpUrlFactory(collection=collection, url="https://example.com")
        dump_url.tdamm_tag = ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        dump_url.tdamm_tag_ml = ["MMA_O_BH", "MMA_O_N"]
        dump_url.save()

        # Migrate to delta
        collection.migrate_dump_to_delta()

        # Create new DumpUrl with updated tags
        updated_dump_url = DumpUrlFactory(collection=collection, url="https://example.com")
        updated_dump_url.tdamm_tag = ["MMA_M_G"]
        updated_dump_url.save()
        collection.migrate_dump_to_delta()

        # Verify tags were updated
        delta_url = DeltaUrl.objects.get(url="https://example.com")
        assert delta_url.tdamm_tag == ["MMA_M_G"]
        assert delta_url.tdamm_tag_manual == ["MMA_M_G"]


@pytest.mark.django_db
class TestTDAMMTagPromotion:
    """Test TDAMM tag behavior during the promotion process"""

    @pytest.fixture
    def collection(self):
        return CollectionFactory()

    def test_tdamm_tags_preserved_in_promotion(self, collection):
        """Test that TDAMM tags are preserved when promoting from Delta to Curated"""
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com")
        delta_url.tdamm_tag = ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        delta_url.tdamm_tag_ml = ["MMA_O_BH", "MMA_O_N"]
        delta_url.save()

        # Promote to curated
        collection.promote_to_curated()

        # Verify tags in the promoted CuratedUrl
        curated_url = CuratedUrl.objects.get(url="https://example.com")
        assert curated_url.tdamm_tag == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert curated_url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert curated_url.tdamm_tag_ml == ["MMA_O_BH", "MMA_O_N"]

    def test_tdamm_tags_updated_in_promotion(self, collection):
        """Test that TDAMM tags are updated during re-promotion"""
        # Initial promotion
        delta_url = DeltaUrlFactory(collection=collection, url="https://example.com")
        delta_url.tdamm_tag = ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        delta_url.tdamm_tag_ml = ["MMA_O_BH", "MMA_O_N"]
        delta_url.save()

        # Promote to curated
        collection.promote_to_curated()

        # Create new DeltaUrl with updated tags
        updated_delta_url = DeltaUrlFactory(collection=collection, url="https://example.com")
        updated_delta_url.tdamm_tag = ["MMA_M_G"]
        updated_delta_url.save()
        collection.promote_to_curated()

        # Verify tags were updated
        curated_url = CuratedUrl.objects.get(url="https://example.com")
        assert curated_url.tdamm_tag == ["MMA_M_G"]
        assert curated_url.tdamm_tag_manual == ["MMA_M_G"]


@pytest.mark.django_db
class TestTDAMMTagUtilityMethods:
    """Test additional TDAMM tag utility methods"""

    def test_get_tag_source_method(self):
        """Test the get_tag_source method for different tag scenarios"""
        url = DeltaUrlFactory()

        # Scenario 1: No tags
        assert url.get_tag_source() == "Not Set"

        # Scenario 2: Only ML tags
        url.tdamm_tag_ml = ["MMA_M_EM"]
        assert url.get_tag_source() == "ml"

        # Scenario 3: Only manual tags
        url.tdamm_tag_ml = None
        url.tdamm_tag = ["MMA_M_G"]
        assert url.get_tag_source() == "manual"

        # Scenario 4: Both ML and manual tags (manual should take precedence)
        url.tdamm_tag_ml = ["MMA_M_EM"]
        assert url.get_tag_source() == "manual"

    def test_add_tag_method(self):
        """Test the add_tag method for different sources"""
        url = DeltaUrlFactory()

        # Prepare initial ml tags
        url.tdamm_tag_ml = ["MMA_O_BH"]

        # Add manual tag since the source was ml
        url.add_tag("MMA_M_G", "ml")
        assert url.tdamm_tag_manual == ["MMA_O_BH", "MMA_M_G"]

        # Add manual tag
        url.add_tag("MMA_M_EM", "manual")
        assert url.tdamm_tag_manual == ["MMA_O_BH", "MMA_M_G", "MMA_M_EM"]
        assert url.tdamm_tag_ml == ["MMA_O_BH"]

        # # Prevent duplicate tags
        url.add_tag("MMA_M_EM", "manual")
        assert url.tdamm_tag_manual == ["MMA_O_BH", "MMA_M_G", "MMA_M_EM"]

    def test_remove_tag_method(self):
        """Test the remove_tag method for different sources"""
        url = DeltaUrlFactory()

        # Prepare initial tags
        url.tdamm_tag_ml = ["MMA_M_EM", "MMA_O_N"]

        # Confirm no manual tags
        assert True if url.tdamm_tag_manual is None else False

        # Remove tag if source was ml
        url.remove_tag("MMA_M_EM", "ml")
        assert url.tdamm_tag_ml == ["MMA_M_EM", "MMA_O_N"]
        assert url.tdamm_tag_manual == ["MMA_O_N"]

        # Remove tag if source was manual
        url.remove_tag("MMA_O_N", "manual")
        assert url.tdamm_tag_manual == []

        # Default to ML tags if manual tags are empty
        assert url.tdamm_tag == ["MMA_M_EM", "MMA_O_N"]
        assert url.tdamm_tag_ml == ["MMA_M_EM", "MMA_O_N"]

    def test_tdamm_tag_collection_method(self):
        """Test the collection method for checking TDAMM tags"""
        collection = CollectionFactory()

        # Create URLs with different tag scenarios
        DeltaUrlFactory(collection=collection, tdamm_tag_manual=["MMA_M_EM"])
        DeltaUrlFactory(collection=collection, tdamm_tag_ml=["MMA_O_BH"])
        DeltaUrlFactory(collection=collection)  # No tags

        # Verify has_tdamm_tags method
        assert collection.has_tdamm_tags() is True

        # Create a new collection with no tagged URLs
        empty_collection = CollectionFactory()
        assert empty_collection.has_tdamm_tags() is False

    def test_ml_source_tag_behavior(self):
        """Test that ML source copies existing list to manual tags"""
        url = DeltaUrlFactory()

        # Set initial ML tags
        url.tdamm_tag_ml = ["MMA_M_EM", "MMA_M_G"]

        # Add tag with ML source - should copy ML tags and add new one
        url.add_tag("MMA_M_N", "ml")
        assert url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert url.tdamm_tag_ml == ["MMA_M_EM", "MMA_M_G"]

    def test_manual_source_tag_behavior(self):
        """Test that manual source only affects manual tags"""
        url = DeltaUrlFactory()
        url.tdamm_tag_ml = ["MMA_M_EM"]
        url.tdamm_tag_manual = ["MMA_M_G"]

        url.add_tag("MMA_M_N", "manual")
        assert url.tdamm_tag_manual == ["MMA_M_G", "MMA_M_N"]
        assert url.tdamm_tag_ml == ["MMA_M_EM"]

    def test_tag_operations_with_none_values(self):
        """Test tag operations when fields are None"""
        url = DeltaUrlFactory()

        # Add tag when both fields are None
        url.add_tag("MMA_M_EM", "manual")
        assert url.tdamm_tag_manual == ["MMA_M_EM"]

        # Remove tag when field is None
        url = DeltaUrlFactory()
        url.remove_tag("MMA_M_EM", "manual")
        assert True if url.tdamm_tag_manual is None else False

    def test_invalid_tag_operations(self):
        """Test operations with invalid tags"""
        url = DeltaUrlFactory()
        url.tdamm_tag_manual = ["MMA_M_EM"]

        # Remove non-existent tag
        url.remove_tag("INVALID_TAG", "manual")
        assert url.tdamm_tag_manual == ["MMA_M_EM"]

    def test_delta_cleanup_after_tag_changes(self):
        """Test DeltaUrl cleanup when tags match CuratedUrl"""
        collection = CollectionFactory()

        # Create matching URLs
        CuratedUrl.objects.create(collection=collection, url="https://example.com", tdamm_tag_manual=["MMA_M_EM"])

        delta = DeltaUrl.objects.create(collection=collection, url="https://example.com")

        # Add same tag - should trigger cleanup
        delta.add_tag("MMA_M_EM", "manual")
        assert not DeltaUrl.objects.filter(id=delta.id).exists()

    def test_curated_url_tag_operations(self):
        """Test that CuratedUrl tag changes create/update DeltaUrl"""
        collection = CollectionFactory()
        curated = CuratedUrl.objects.create(collection=collection, url="https://example.com", tdamm_tag_manual=[])

        # Initial state
        curated.tdamm_tag_manual = []
        curated.save()

        # Adding tag should create DeltaUrl with different tags
        curated.add_tag("MMA_M_EM", "manual")
        delta = DeltaUrl.objects.get(url=curated.url)
        assert delta.tdamm_tag_manual == ["MMA_M_EM"]

        # Adding another tag should update existing DeltaUrl
        curated.add_tag("MMA_M_G", "manual")
        delta.refresh_from_db()
        assert len(DeltaUrl.objects.filter(url=curated.url)) == 1
        assert delta.tdamm_tag_manual == ["MMA_M_G"]

    def test_curated_url_ml_tag_operations(self):
        """Test CuratedUrl operations with ML source"""
        collection = CollectionFactory()
        curated = CuratedUrl.objects.create(
            collection=collection, url="https://example.com", tdamm_tag_ml=["MMA_M_EM", "MMA_M_G"]
        )

        # Adding tag with ML source should copy ML tags to manual
        curated.add_tag("MMA_M_N", "ml")
        delta = DeltaUrl.objects.get(url=curated.url)
        assert delta.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert delta.tdamm_tag_ml == ["MMA_M_EM", "MMA_M_G"]

    def test_ml_source_cleanup_behavior(self):
        """Test cleanup when using ML source"""
        url = DeltaUrlFactory()
        url.tdamm_tag_ml = ["MMA_M_EM", "MMA_M_G"]

        # Using ML source should copy to manual
        url.add_tag("MMA_M_N", "ml")
        assert url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G", "MMA_M_N"]
        assert url.tdamm_tag_ml == ["MMA_M_EM", "MMA_M_G"]

        # Removing via ML source should update manual
        url.remove_tag("MMA_M_N", "ml")
        assert url.tdamm_tag_manual == ["MMA_M_EM", "MMA_M_G"]

    def test_tag_source_transitions(self):
        """Test transitioning between tag sources"""
        url = DeltaUrlFactory()

        # Start with ML tags
        url.tdamm_tag_ml = ["MMA_M_EM"]
        assert url.get_tag_source() == "ml"

        # Add manual tag should change source
        url.add_tag("MMA_M_G", "manual")
        assert url.get_tag_source() == "manual"

        # Clear manual tags should revert to ML
        url.tdamm_tag_manual = []
        assert url.get_tag_source() == "ml"

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
        assert url.tdamm_tag_ml == []

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

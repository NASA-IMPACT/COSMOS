# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/test_tdamm_tags.py

import pytest

from sde_collections.tests.factories import CandidateURLFactory


@pytest.mark.django_db
class TestTDAMMFields:
    def test_tdamm_switch_behavior(self):
        """Test that TDAMM fields only work when switch is enabled"""
        # Create URL with TDAMM disabled
        url = CandidateURLFactory(is_tdamm=False)
        url.tdamm_tag = ["MMA_M_EM"]
        assert url.tdamm_tag is None
        assert url.tdamm_tag_manual is None
        assert url.tdamm_tag_ml is None

        # Enable TDAMM
        url.is_tdamm = True
        url.save()
        url.tdamm_tag = ["MMA_M_EM"]
        assert url.tdamm_tag == ["MMA_M_EM"]
        assert url.tdamm_tag_manual == ["MMA_M_EM"]

    def test_manual_and_ml_field_behavior(self):
        """Test the relationship between manual and ML fields"""
        url = CandidateURLFactory(is_tdamm=True)

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
        url = CandidateURLFactory(is_tdamm=True)

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
        url = CandidateURLFactory(is_tdamm=True)

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
        url = CandidateURLFactory(is_tdamm=True)

        # Set both manual and ML tags
        url.tdamm_tag = ["MMA_M_EM"]
        url.tdamm_tag_ml = ["MMA_M_G"]

        # Delete tdamm_tag
        del url.tdamm_tag
        assert url.tdamm_tag_manual is None
        assert url.tdamm_tag_ml is None

    def test_multiple_tags(self):
        """Test handling of multiple tags"""
        url = CandidateURLFactory(is_tdamm=True)

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
        url = CandidateURLFactory(is_tdamm=True)

        # Set values
        url.tdamm_tag = ["MMA_M_EM"]
        url.tdamm_tag_ml = ["MMA_M_G"]
        url.save()

        # Refresh from database
        url.refresh_from_db()
        assert url.tdamm_tag_manual == ["MMA_M_EM"]
        assert url.tdamm_tag_ml == ["MMA_M_G"]

# inference/tests/test_classification_utils.py
# docker-compose -f local.yml run --rm django pytest inference/tests/test_classification_utils.py

from unittest.mock import Mock, patch

import pytest

from inference.utils.classification_utils import (
    map_classification_to_tdamm_tags,
    update_url_with_classification_results,
)


class TestMapClassificationToTDAMMTags:
    """Tests for the map_classification_to_tdamm_tags function"""

    def test_basic_mapping(self):
        """Test basic mapping of classification results to TDAMM tags"""
        classification_results = {"Optical": 0.9, "Infrared": 0.85, "X-rays": 0.95}

        expected_tags = [
            "MMA_M_EM_O",  # Optical
            "MMA_M_EM_I",  # Infrared
            "MMA_M_EM_X",  # X-rays
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_threshold_handling(self):
        """Test that only tags above the threshold are included"""
        classification_results = {
            "Optical": 0.9,  # Above threshold
            "Infrared": 0.55,  # Below threshold
            "X-rays": 0.7,  # Below threshold
            "Radio": 0.85,  # Above threshold
        }

        expected_tags = [
            "MMA_M_EM_O",  # Optical
            "MMA_M_EM_R",  # Radio
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_case_insensitivity(self):
        """Test that the mapping works regardless of case"""
        classification_results = {
            "optical": 0.9,  # Lowercase
            "INFRARED": 0.85,  # Uppercase
            "X-Rays": 0.95,  # Mixed case
        }

        expected_tags = [
            "MMA_M_EM_O",  # Optical
            "MMA_M_EM_I",  # Infrared
            "MMA_M_EM_X",  # X-rays
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_special_cases(self):
        """Test special case mappings"""
        classification_results = {
            "non-TDAMM": 0.95,
            "supernovae": 0.9,
        }

        expected_tags = [
            "NOT_TDAMM",
            "MMA_S_SU",
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_string_confidence_values(self):
        """Test handling string confidence values"""
        classification_results = {"Optical": "0.9", "Infrared": 0.85, "X-rays": "0.95"}  # String  # Float  # String

        expected_tags = [
            "MMA_M_EM_O",  # Optical
            "MMA_M_EM_I",  # Infrared
            "MMA_M_EM_X",  # X-rays
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_invalid_confidence_values(self):
        """Test handling invalid confidence values"""
        classification_results = {"Optical": 0.9, "Infrared": "not_a_number", "X-rays": 0.95}

        expected_tags = [
            "MMA_M_EM_O",  # Optical
            "MMA_M_EM_X",  # X-rays
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    def test_empty_classification_results(self):
        """Test handling of empty classification results"""
        classification_results = {}

        actual_tags = map_classification_to_tdamm_tags(classification_results)
        assert actual_tags == []

    def test_complex_mappings(self):
        """Test more complex mappings with specific TDAMM categories"""
        classification_results = {
            "Binary Black Holes": 0.9,
            "Neutron Star-Black Hole": 0.85,
            "Gamma-ray Bursts": 0.95,
            "Fast Blue Optical Transients": 0.8,
        }

        expected_tags = [
            "MMA_O_BI_BBH",  # Binary Black Holes
            "MMA_O_BI_N",  # Neutron Star-Black Hole
            "MMA_S_G",  # Gamma-ray Bursts
            "MMA_S_FBOT",  # Fast Blue Optical Transients
        ]

        actual_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.8)
        assert sorted(actual_tags) == sorted(expected_tags)

    @patch("django.conf.settings.TDAMM_CLASSIFICATION_THRESHOLD", 0.75)
    def test_default_threshold_from_settings(self):
        """Test using the default threshold from settings"""
        classification_results = {"Optical": 0.7, "Infrared": 0.8, "X-rays": 0.9}

        # With settings threshold of 0.75, Infrared and X-rays should be included
        expected_tags = ["MMA_M_EM_I", "MMA_M_EM_X"]
        actual_tags = map_classification_to_tdamm_tags(classification_results)  # No threshold provided

        assert sorted(actual_tags) == sorted(expected_tags)


class TestUpdateUrlWithClassificationResults:
    """Tests for the update_url_with_classification_results function"""

    @pytest.fixture
    def mock_url(self):
        """Create a mock URL object for testing"""
        url = Mock()
        url.tdamm_tag_ml = None
        url.save = Mock()
        return url

    @patch("inference.utils.classification_utils.map_classification_to_tdamm_tags")
    def test_update_url_properly_calls_mapping(self, mock_map_function, mock_url):
        """Test that URL objects are correctly updated with TDAMM tags"""
        # Set up mock return value
        mock_tdamm_tags = ["MMA_M_EM_O", "MMA_M_EM_X"]
        mock_map_function.return_value = mock_tdamm_tags

        # Test data
        classification_results = {"Optical": 0.9, "X-rays": 0.85}

        # Call the function
        result = update_url_with_classification_results(mock_url, classification_results)

        # Verify map_classification_to_tdamm_tags was called properly
        mock_map_function.assert_called_once_with(classification_results)

        # Verify URL object was updated correctly
        assert mock_url.tdamm_tag_ml == mock_tdamm_tags
        mock_url.save.assert_called_once_with(update_fields=["tdamm_tag_ml"])

        # Verify return value
        assert result == mock_tdamm_tags

    @patch("inference.utils.classification_utils.map_classification_to_tdamm_tags")
    def test_threshold_parameter_behavior(self, mock_map_function, mock_url):
        """Test how threshold parameter is handled"""
        mock_tdamm_tags = ["MMA_M_EM_O"]
        mock_map_function.return_value = mock_tdamm_tags

        classification_results = {"Optical": 0.9}
        custom_threshold = 0.85

        update_url_with_classification_results(mock_url, classification_results, threshold=custom_threshold)

        # Based on the implementation, the function doesn't pass the threshold parameter
        mock_map_function.assert_called_once_with(classification_results)

    def test_integration_with_real_mapping(self, mock_url):
        """Test end-to-end integration with real mapping function"""
        classification_results = {"Optical": 0.9, "Binary Black Holes": 0.85, "Novae": 0.8}

        expected_tags = ["MMA_M_EM_O", "MMA_O_BI_BBH", "MMA_S_N"]

        result = update_url_with_classification_results(mock_url, classification_results, threshold=0.7)

        assert sorted(result) == sorted(expected_tags)
        assert sorted(mock_url.tdamm_tag_ml) == sorted(expected_tags)

    def test_full_mapping_coverage(self):
        """Test that all provided mappings work correctly"""
        mapping = {
            "Optical": "MMA_M_EM_O",
            "Ultraviolet": "MMA_M_EM_U",
            "Exoplanets": "MMA_O_E",
            "Gamma rays": "MMA_M_EM_G",
            "Infrared": "MMA_M_EM_I",
            "Gamma-ray Bursts": "MMA_S_G",
            "SuperNovae": "MMA_S_SU",
            "non-TDAMM": "NOT_TDAMM",
            "Radio": "MMA_M_EM_R",
            "White Dwarf Binaries": "MMA_O_BI_W",
            "Pulsar Wind Nebulae": "MMA_O_N_PWN",
            "X-rays": "MMA_M_EM_X",
            "Compact Binary Inspiral": "MMA_M_G_CBI",
            "Stochastic": "MMA_M_G_S",
            "Continuous": "MMA_M_G_CON",
            "Supernova Remnants": "MMA_O_S",
            "Stellar flares": "MMA_S_ST",
            "Pulsars": "MMA_O_N_P",
            "Neutron Star-Black Hole": "MMA_O_BI_N",
            "Cosmic Rays": "MMA_M_C",
            "Binary Black Holes": "MMA_O_BI_BBH",
            "Burst": "MMA_M_G_B",
            "Binary Neutron Stars": "MMA_O_BI_BNS",
            "Fast Blue Optical Transients": "MMA_S_FBOT",
            "Cataclysmic Variables": "MMA_O_BI_C",
            "Binary Pulsars": "MMA_O_BI_B",
            "Active Galactic Nuclei": "MMA_O_BH_AGN",
            "Neutrinos": "MMA_M_N",
            "Fast Radio Bursts": "MMA_S_F",
            "Stellar Mass": "MMA_O_BH_STM",
            "Magnetars": "MMA_O_N_M",
            "Pevatrons": "MMA_S_P",
            "Novae": "MMA_S_N",
            "Kilonovae": "MMA_S_K",
            "Supermassive": "MMA_O_BH_SUM",
            "Intermediate Mass": "MMA_O_BH_IM",
        }

        # Create classification results with all keys
        classification_results = {key: 1.0 for key in mapping.keys()}

        # Map to TDAMM tags
        tdamm_tags = map_classification_to_tdamm_tags(classification_results, threshold=0.5)

        # Verify all expected tags are present
        assert sorted(tdamm_tags) == sorted(list(mapping.values()))

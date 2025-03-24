# inference/tests/test_threshold_processor.py
# docker-compose -f local.yml run --rm django pytest inference/tests/test_threshold_processor.py

from unittest.mock import patch

import pytest

from inference.utils.threshold_processor import ClassificationThresholdProcessor


class TestClassificationThresholdProcessor:
    """Test suite for ClassificationThresholdProcessor class."""

    @pytest.fixture
    def test_thresholds(self):
        """Test thresholds for generic processor."""
        return {"TAG_A": 0.7, "TAG_B": 0.5, "TAG_C": 0.8}

    @pytest.fixture
    def processor(self, test_thresholds):
        """Create a ClassificationThresholdProcessor with test thresholds."""
        return ClassificationThresholdProcessor(test_thresholds, default_threshold=0.6)

    def test_initialization(self, test_thresholds):
        """Test initialization with provided thresholds."""
        processor = ClassificationThresholdProcessor(test_thresholds, default_threshold=0.6)
        assert processor.thresholds == test_thresholds
        assert processor.default_threshold == 0.6

    def test_for_tdamm_factory(self):
        """Test the for_tdamm class factory method."""
        with patch("inference.utils.threshold_processor.TDAMM_TAG_THRESHOLDS", {"TAG1": 0.7}), patch(
            "inference.utils.threshold_processor.DEFAULT_TDAMM_THRESHOLD", 0.5
        ):
            processor = ClassificationThresholdProcessor.for_tdamm()
            assert processor.thresholds == {"TAG1": 0.7}
            assert processor.default_threshold == 0.5

    def test_for_division_factory(self):
        """Test the for_division class factory method."""
        with patch("inference.utils.threshold_processor.DIVISION_TAG_THRESHOLDS", {1: 0.7}), patch(
            "inference.utils.threshold_processor.DEFAULT_DIVISION_THRESHOLD", 0.5
        ):
            processor = ClassificationThresholdProcessor.for_division()
            assert processor.thresholds == {1: 0.7}
            assert processor.default_threshold == 0.5

    def test_get_threshold_exact_match(self, processor):
        """Test get_threshold with an exact tag match."""
        assert processor.get_threshold("TAG_A") == 0.7
        assert processor.get_threshold("TAG_B") == 0.5
        assert processor.get_threshold("TAG_C") == 0.8

    def test_get_threshold_no_match(self, processor):
        """Test get_threshold with a tag that doesn't exist."""
        assert processor.get_threshold("UNKNOWN_TAG") == 0.6  # default threshold

    def test_filter_classifications_all_pass(self, processor):
        """Test filter_classifications where all pass their thresholds."""
        classifications = {
            "TAG_A": 0.8,  # 0.8 > 0.7 threshold
            "TAG_B": 0.6,  # 0.6 > 0.5 threshold
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 2
        assert "TAG_A" in filtered
        assert "TAG_B" in filtered

    def test_filter_classifications_some_pass(self, processor):
        """Test filter_classifications where some pass their thresholds."""
        classifications = {
            "TAG_A": 0.6,  # 0.6 < 0.7 threshold
            "TAG_B": 0.6,  # 0.6 > 0.5 threshold
            "TAG_C": 0.9,  # 0.9 > 0.8 threshold
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 2
        assert "TAG_A" not in filtered
        assert "TAG_B" in filtered
        assert "TAG_C" in filtered

    def test_filter_classifications_none_pass(self, processor):
        """Test filter_classifications where none pass their thresholds."""
        classifications = {
            "TAG_A": 0.6,  # 0.6 < 0.7 threshold
            "TAG_C": 0.7,  # 0.7 < 0.8 threshold
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 0

    def test_filter_classifications_default_threshold(self, processor):
        """Test filter_classifications using default threshold for unknown tags."""
        classifications = {
            "UNKNOWN_TAG": 0.7,  # 0.7 > 0.6 default threshold
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 1
        assert "UNKNOWN_TAG" in filtered

    def test_filter_classifications_string_confidence(self, processor):
        """Test filter_classifications with string confidence values."""
        classifications = {
            "TAG_A": "0.8",  # Should convert to float and pass
            "TAG_B": "0.4",  # Should convert to float and fail
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 1
        assert "TAG_A" in filtered
        assert "TAG_B" not in filtered

    def test_filter_classifications_invalid_confidence(self, processor):
        """Test filter_classifications with invalid confidence values."""
        classifications = {
            "TAG_A": 0.8,
            "TAG_B": "not a number",  # Invalid
            "TAG_C": 0.9,
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 2
        assert "TAG_A" in filtered
        assert "TAG_B" not in filtered
        assert "TAG_C" in filtered

    def test_filter_classifications_exact_threshold(self, processor):
        """Test filter_classifications with confidence exactly at threshold."""
        classifications = {
            "TAG_A": 0.7,  # Exactly at threshold (0.7)
            "TAG_B": 0.5,  # Exactly at threshold (0.5)
        }
        filtered = processor.filter_classifications(classifications)
        assert len(filtered) == 2
        assert "TAG_A" in filtered
        assert "TAG_B" in filtered

    def test_filter_classifications_empty_dict(self, processor):
        """Test filter_classifications with an empty dictionary."""
        filtered = processor.filter_classifications({})
        assert filtered == {}

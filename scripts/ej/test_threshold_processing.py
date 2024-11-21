"""Unit tests for threshold processing functionality."""

import pytest
from threshold_processing import ThresholdProcessor


class TestThresholdProcessor:
    """Test suite for ThresholdProcessor class."""

    @pytest.fixture
    def default_thresholds(self):
        """Default thresholds for testing."""
        return {
            "Not EJ": 0.80,
            "Urban Flooding": 0.50,
            "Extreme Heat": 0.50,
            "Water Availability": 0.80,
            "Health & Air Quality": 0.90,
            "Disasters": 0.80,
            "Food Availability": 0.80,
            "Human Dimensions": 0.80,
        }

    @pytest.fixture
    def authorized_classifications(self):
        """Authorized classifications for testing."""
        return [
            "Urban Flooding",
            "Extreme Heat",
            "Water Availability",
            "Health & Air Quality",
            "Disasters",
            "Food Availability",
            "Human Dimensions",
        ]

    @pytest.fixture
    def processor(self, default_thresholds):
        """Create a ThresholdProcessor instance with test thresholds."""
        return ThresholdProcessor(thresholds=default_thresholds)

    @pytest.fixture
    def custom_processor(self):
        """Create a ThresholdProcessor instance with simplified test thresholds."""
        custom_thresholds = {
            "Not EJ": 0.75,
            "Test Category 1": 0.60,
            "Test Category 2": 0.80,
        }
        return ThresholdProcessor(thresholds=custom_thresholds)

    def test_initialization_with_thresholds(self, processor, default_thresholds):
        """Test initialization with provided thresholds."""
        assert processor.thresholds == default_thresholds
        assert "Not EJ" in processor.thresholds
        assert processor.thresholds["Not EJ"] == 0.80

    def test_initialization_custom_thresholds(self, custom_processor):
        """Test initialization with custom thresholds."""
        assert custom_processor.thresholds["Not EJ"] == 0.75
        assert custom_processor.thresholds["Test Category 1"] == 0.60
        assert custom_processor.thresholds["Test Category 2"] == 0.80

    def test_single_high_scoring_not_ej(self, processor):
        """Test when 'Not EJ' has the highest score."""
        predictions = [
            {"label": "Not EJ", "score": 0.90},
            {"label": "Urban Flooding", "score": 0.85},
            {"label": "Water Availability", "score": 0.82},
        ]
        result = processor.process_predictions(predictions)
        assert result == ["Not EJ"]
        assert len(result) == 1

    def test_multiple_indicators_above_threshold(self, processor):
        """Test when multiple indicators exceed their thresholds."""
        predictions = [
            {"label": "Not EJ", "score": 0.30},
            {"label": "Urban Flooding", "score": 0.75},  # Above 0.50 threshold
            {"label": "Extreme Heat", "score": 0.60},  # Above 0.50 threshold
            {"label": "Water Availability", "score": 0.85},  # Above 0.80 threshold
        ]
        result = processor.process_predictions(predictions)
        assert len(result) == 3
        assert "Urban Flooding" in result
        assert "Extreme Heat" in result
        assert "Water Availability" in result

    def test_no_indicators_above_threshold(self, processor):
        """Test when no indicators meet their thresholds."""
        predictions = [
            {"label": "Not EJ", "score": 0.70},
            {"label": "Urban Flooding", "score": 0.45},  # Below 0.50 threshold
            {"label": "Water Availability", "score": 0.75},  # Below 0.80 threshold
        ]
        result = processor.process_predictions(predictions)
        assert result == ["Not EJ"]

    def test_mixed_threshold_scenarios(self, processor):
        """Test various mixed scenarios of threshold checking."""
        predictions = [
            {"label": "Not EJ", "score": 0.60},
            {"label": "Urban Flooding", "score": 0.55},  # Above 0.50 threshold
            {"label": "Extreme Heat", "score": 0.45},  # Below 0.50 threshold
            {"label": "Water Availability", "score": 0.85},  # Above 0.80 threshold
        ]
        result = processor.process_predictions(predictions)
        assert len(result) == 2
        assert "Urban Flooding" in result
        assert "Water Availability" in result
        assert "Extreme Heat" not in result

    def test_authorized_classifications_filtering(self, processor, authorized_classifications):
        """Test filtering of authorized classifications."""
        # Monkey patch the authorized classifications for this test
        import threshold_processing

        original_authorized = threshold_processing.AUTHORIZED_CLASSIFICATIONS
        threshold_processing.AUTHORIZED_CLASSIFICATIONS = authorized_classifications

        test_classifications = ["Urban Flooding", "Invalid Category", "Water Availability", "Another Invalid"]
        result = processor.filter_authorized_classifications(test_classifications)
        assert len(result) == 2
        assert all(r in authorized_classifications for r in result)
        assert "Invalid Category" not in result
        assert "Another Invalid" not in result

        # Restore original authorized classifications
        threshold_processing.AUTHORIZED_CLASSIFICATIONS = original_authorized

    def test_process_and_filter_complete_pipeline(self, processor, authorized_classifications):
        """Test the complete processing pipeline with unauthorized categories."""
        # Monkey patch the authorized classifications for this test
        import threshold_processing

        original_authorized = threshold_processing.AUTHORIZED_CLASSIFICATIONS
        threshold_processing.AUTHORIZED_CLASSIFICATIONS = authorized_classifications

        predictions = [
            {"label": "Not EJ", "score": 0.30},
            {"label": "Urban Flooding", "score": 0.75},
            {"label": "Invalid Category", "score": 0.95},
            {"label": "Water Availability", "score": 0.85},
        ]
        result = processor.process_and_filter(predictions)
        assert len(result) == 2
        assert "Urban Flooding" in result
        assert "Water Availability" in result
        assert "Invalid Category" not in result

        # Restore original authorized classifications
        threshold_processing.AUTHORIZED_CLASSIFICATIONS = original_authorized

    def test_edge_case_empty_predictions(self, processor):
        """Test handling of empty predictions list."""
        result = processor.process_predictions([])
        assert result == ["Not EJ"]

    def test_edge_case_missing_scores(self, processor):
        """Test handling of predictions with missing scores."""
        predictions = [{"label": "Urban Flooding"}, {"label": "Water Availability", "score": 0.85}]  # Missing score
        with pytest.raises(KeyError):
            processor.process_predictions(predictions)

    def test_edge_case_invalid_score_values(self, processor):
        """Test handling of invalid score values."""
        predictions = [{"label": "Not EJ", "score": "invalid"}, {"label": "Urban Flooding", "score": 0.75}]
        with pytest.raises(TypeError):
            processor.process_predictions(predictions)

    def test_threshold_boundary_conditions(self, processor):
        """Test classification at exact threshold boundaries."""
        predictions = [
            {"label": "Not EJ", "score": 0.30},
            {"label": "Urban Flooding", "score": 0.50},  # Exactly at threshold
            {"label": "Water Availability", "score": 0.80},  # Exactly at threshold
            {"label": "Health & Air Quality", "score": 0.89},  # Just below threshold
        ]
        result = processor.process_predictions(predictions)
        assert len(result) == 2
        assert "Urban Flooding" in result
        assert "Water Availability" in result
        assert "Health & Air Quality" not in result

    def test_all_indicators_same_score(self, processor):
        """Test behavior when all indicators have the same score."""
        predictions = [
            {"label": "Not EJ", "score": 0.85},
            {"label": "Urban Flooding", "score": 0.85},
            {"label": "Water Availability", "score": 0.85},
        ]
        result = processor.process_predictions(predictions)
        assert result == ["Not EJ"]  # Since Not EJ is highest scoring (tied) prediction

    def test_high_scores_below_threshold(self, processor):
        """Test when scores are high but still below their respective thresholds."""
        predictions = [
            {"label": "Not EJ", "score": 0.70},
            {"label": "Health & Air Quality", "score": 0.89},  # High but below 0.90 threshold
            {"label": "Water Availability", "score": 0.79},  # High but below 0.80 threshold
        ]
        result = processor.process_predictions(predictions)
        assert result == ["Not EJ"]


if __name__ == "__main__":
    pytest.main([__file__])

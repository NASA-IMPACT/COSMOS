"""Module for processing classifications with tag-specific thresholds."""

from inference.utils.config import (
    DEFAULT_DIVISION_THRESHOLD,
    DEFAULT_TDAMM_THRESHOLD,
    DIVISION_TAG_THRESHOLDS,
    TDAMM_TAG_THRESHOLDS,
)


class ClassificationThresholdProcessor:
    """
    Generic processor for classifications using tag-specific thresholds.
    Can be used with any classification system where different classes
    need different confidence thresholds.
    """

    def __init__(self, thresholds: dict[str, float], default_threshold: float = 0.5):
        """
        Initialize the processor with thresholds.

        Args:
            thresholds: Dictionary of classification tags and their threshold values.
            default_threshold: Default threshold to use if tag isn't in thresholds.
        """
        self.thresholds = thresholds
        self.default_threshold = default_threshold

    @classmethod
    def for_tdamm(cls):
        """Create a processor for TDAMM classification."""
        return cls(TDAMM_TAG_THRESHOLDS, DEFAULT_TDAMM_THRESHOLD)

    @classmethod
    def for_division(cls):
        """Create a processor for Division classification."""
        return cls(DIVISION_TAG_THRESHOLDS, DEFAULT_DIVISION_THRESHOLD)

    def get_threshold(self, tag: str) -> float:
        """
        Get the threshold for a tag.

        Args:
            tag: The tag to get threshold for

        Returns:
            The threshold value as a float
        """
        return self.thresholds.get(tag, self.default_threshold)

    def filter_classifications(self, classifications: dict[str, float | str]) -> dict[str, float]:
        """
        Filter classifications based on their thresholds.

        Args:
            classifications: Dictionary with classification keys and confidence scores

        Returns:
            Dictionary with classifications that passed their thresholds
        """
        result = {}
        for key, confidence in classifications.items():
            # Convert confidence to float if it's a string
            if isinstance(confidence, str):
                try:
                    confidence_value = float(confidence)
                except (ValueError, TypeError):
                    continue
            else:
                confidence_value = confidence

            # Get the threshold for this classification
            threshold = self.get_threshold(key)

            # Keep only classifications that meet their threshold
            if confidence_value >= threshold:
                result[key] = confidence_value

        return result

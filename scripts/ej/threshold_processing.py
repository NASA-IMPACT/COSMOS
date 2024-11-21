"""Module for processing classification predictions with thresholds."""

try:
    from config import AUTHORIZED_CLASSIFICATIONS, INDICATOR_THRESHOLDS
except ImportError:
    from scripts.ej.config import AUTHORIZED_CLASSIFICATIONS, INDICATOR_THRESHOLDS


class ThresholdProcessor:
    """
    Processes classification predictions using configurable thresholds.
    """

    def __init__(self, thresholds: dict[str, float] = None):
        """
        Initialize the processor with thresholds.

        Args:
            thresholds: Dictionary of classification labels and their threshold values.
                       If None, uses default thresholds from config.
        """
        self.thresholds = thresholds or INDICATOR_THRESHOLDS

    def process_predictions(self, predictions: list[dict[str, float]]) -> list[str]:
        """
        Process predictions and classify based on individual thresholds.

        Args:
            predictions: List of dictionaries containing prediction labels and scores.
                       Each dict should have 'label' and 'score' keys.

        Returns:
            List of classification labels that meet their respective thresholds.
        """
        # Find highest scoring prediction
        highest_prediction = max(predictions, key=lambda x: x["score"])

        # If highest prediction is "Not EJ", return it as the only classification
        if highest_prediction["label"] == "Not EJ":
            return ["Not EJ"]

        # Filter classifications based on thresholds
        classifications = [
            pred["label"]
            for pred in predictions
            if (pred["score"] >= self.thresholds[pred["label"]] and pred["label"] != "Not EJ")
        ]

        # Default to "Not EJ" if no classifications meet thresholds
        return classifications if classifications else ["Not EJ"]

    def filter_authorized_classifications(self, classifications: list[str]) -> list[str]:
        """
        Filter classifications to keep only authorized ones.

        Args:
            classifications: List of classification labels.

        Returns:
            List of authorized classification labels.
        """
        return [cls for cls in classifications if cls in AUTHORIZED_CLASSIFICATIONS]

    def process_and_filter(self, predictions: list[dict[str, float]]) -> list[str]:
        """
        Process predictions and filter to authorized classifications.

        Args:
            predictions: List of dictionaries containing prediction labels and scores.

        Returns:
            List of authorized classification labels that meet their thresholds.
        """
        classifications = self.process_predictions(predictions)
        return self.filter_authorized_classifications(classifications)

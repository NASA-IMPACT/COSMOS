from django.conf import settings

from inference.utils.threshold_processor import ClassificationThresholdProcessor
from sde_collections.models.collection_choice_fields import TDAMMTags


def map_classification_to_tdamm_tags(classification_results, threshold=None):
    """
    Map classification confidence scores to TDAMM tags.

    Args:
        classification_results (dict): Dictionary of tag names and confidence scores
        threshold (float, optional): Confidence threshold to consider a tag as applicable
                                    If None, uses settings.TDAMM_CLASSIFICATION_THRESHOLD

    Returns:
        list: List of TDAMM tag values that exceed the threshold
    """
    if threshold is None:
        threshold = float(getattr(settings, "TDAMM_CLASSIFICATION_THRESHOLD"))

    # Initialize the threshold processor
    threshold_processor = ClassificationThresholdProcessor.for_tdamm()

    selected_tags = []

    # Build a mapping from simplified tag names to actual TDAMMTags values
    tag_mapping = {}
    for tag_value, display_name in TDAMMTags.choices:
        # Extract the last part of the display name (most specific part)
        parts = display_name.split(" - ")
        simplified_name = parts[-1].lower()
        tag_mapping[simplified_name] = tag_value

        # Handling naming inconsistencies
        if display_name == "Not TDAMM":
            tag_mapping["non-tdamm"] = tag_value
        if simplified_name == "supernovae":
            tag_mapping["supernovae"] = tag_value

    # Process classification results
    tdamm_confidences = {}
    for classification_key, confidence in classification_results.items():
        if isinstance(confidence, str):
            try:
                confidence = float(confidence)
            except (ValueError, TypeError):
                continue

        # Normalize the classification key
        normalized_key = classification_key.lower()
        tag_value = None

        # Try to find a match in our mapping
        if normalized_key in tag_mapping:
            tag_value = tag_mapping[normalized_key]
        else:
            # Try partial matching
            for key, value in tag_mapping.items():
                if key in normalized_key or normalized_key in key:
                    tag_value = value
                    break

        # Skip if no matching tag found
        if not tag_value:
            continue

        tdamm_confidences[tag_value] = confidence

    selected_tags = threshold_processor.filter_classifications(tdamm_confidences)
    return list(selected_tags.keys())


def update_url_with_classification_results(url_object, classification_results, threshold=None):
    """
    Update a URL object with TDAMM tags based on classification results.

    Args:
        url_object: A BaseUrl derived object (DumpUrl, DeltaUrl, CuratedUrl)
        classification_results (dict): Dictionary of tag names and confidence scores
        threshold (float, optional): Confidence threshold to consider a tag as applicable
    Returns:
        list: The list of TDAMM tags that were applied
    """
    tdamm_tags = map_classification_to_tdamm_tags(classification_results, threshold=threshold)

    # Update the URL object
    url_object.tdamm_tag_ml = tdamm_tags
    url_object.save(update_fields=["tdamm_tag_ml"])

    return tdamm_tags

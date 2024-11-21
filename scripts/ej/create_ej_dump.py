"""
Creates EJ dump files by processing CMR data and classifications.
"""

import json
from datetime import datetime

from cmr_processing import CmrDataset
from threshold_processing import ThresholdProcessor

from config import (
    CMR_FILENAME,
    INFERENCE_FILENAME,
    OUTPUT_FILENAME_TEMPLATE,
    TIMESTAMP_FORMAT,
)


def load_json_file(file_path: str) -> dict:
    """Load and parse a JSON file."""
    with open(file_path) as file:
        return json.load(file)


def save_to_json(data: dict | list, file_path: str) -> None:
    """Save data to a JSON file with proper formatting."""
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def create_cmr_dict(cmr_data: list[dict]) -> dict[str, dict]:
    """
    Restructure CMR data into a dictionary with concept-id as the key.

    Args:
        cmr_data: List of CMR dataset dictionaries.

    Returns:
        Dictionary mapping concept-ids to their respective CMR data.
    """
    return {dataset["meta"]["concept-id"]: dataset for dataset in cmr_data}


def create_clean_dataset(
    inferences: list[dict],
    cmr_dict: dict[str, dict],
    processor: ThresholdProcessor,
) -> list[dict]:
    """
    Create clean dataset with processed CMR data and classifications.
    Excludes datasets classified as 'Not EJ'.

    Args:
        inferences: List of inference dictionaries containing predictions.
        cmr_dict: Dictionary mapping concept-ids to CMR data.
        processor: ThresholdProcessor instance for processing classifications.

    Returns:
        List of processed dataset dictionaries, excluding 'Not EJ' classifications.
    """
    clean_data = []

    for inference in inferences:
        concept_id = inference["concept-id"]
        cmr_dataset = cmr_dict.get(concept_id)

        if cmr_dataset:
            # Process classifications
            classifications = processor.process_and_filter(inference["predictions"])

            # Only include datasets that have valid classifications and are not marked as 'Not EJ'
            if classifications and "Not EJ" not in classifications:
                # Process CMR data
                processed_cmr = CmrDataset(cmr_dataset).to_dict()
                processed_cmr["indicators"] = ";".join(classifications)
                clean_data.append(processed_cmr)

    return clean_data


def main(
    cmr_file: str = CMR_FILENAME,
    inference_file: str = INFERENCE_FILENAME,
) -> None:
    """
    Main function to create EJ dump file.

    Args:
        cmr_file: Path to the CMR data JSON file.
        inference_file: Path to the inference predictions JSON file.
    """
    # Initialize processor
    processor = ThresholdProcessor()

    # Load input files
    inferences = load_json_file(inference_file)
    cmr = load_json_file(cmr_file)

    # Create CMR dictionary
    cmr_dict = create_cmr_dict(cmr)

    # Create clean dataset with all required fields, excluding 'Not EJ' classifications
    clean_data = create_clean_dataset(
        inferences=inferences,
        cmr_dict=cmr_dict,
        processor=processor,
    )

    # Generate output filename with timestamp
    timestamp = datetime.now().strftime(TIMESTAMP_FORMAT)
    output_filename = OUTPUT_FILENAME_TEMPLATE.format(timestamp)

    # Save output
    save_to_json(clean_data, output_filename)
    print(f"Processed {len(clean_data)} EJ datasets from {cmr_file} and {inference_file}")
    print()
    print(f"Saved to {output_filename}")


if __name__ == "__main__":
    main(
        cmr_file=CMR_FILENAME,
        inference_file=INFERENCE_FILENAME,
    )

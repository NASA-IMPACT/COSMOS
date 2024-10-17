"""
inferences are supplied by the classification model. the contact point is Bishwas
cmr is supplied by running
github.com/NASA-IMPACT/llm-app-EJ-classifier/blob/develop/scripts/data_processing/download_cmr.py
move to the server like this: scp ej_dump_20241017_133151.json  sde:/home/ec2-user/sde_indexing_helper/backups/
"""

import json
from datetime import datetime


def load_json_file(file_path: str) -> dict:
    with open(file_path) as file:
        return json.load(file)


def save_to_json(data: dict | list, file_path: str) -> None:
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)


def process_classifications(predictions: list[dict[str, float]], thresholds: dict[str, float]) -> list[str]:
    """
    Process the predictions and classify based on the individual thresholds per indicator:
    1. If 'Not EJ' is the highest scoring prediction, return 'Not EJ' as the only classification.
    2. Filter classifications based on their individual thresholds, excluding 'Not EJ'.
    3. Default to 'Not EJ' if no classifications meet the threshold.
    """
    highest_prediction = max(predictions, key=lambda x: x["score"])

    if highest_prediction["label"] == "Not EJ":
        return ["Not EJ"]

    classifications = [
        pred["label"]
        for pred in predictions
        if pred["score"] >= thresholds[pred["label"]] and pred["label"] != "Not EJ"
    ]

    return classifications if classifications else ["Not EJ"]


def create_cmr_dict(cmr_data: list[dict[str, dict[str, str]]]) -> dict[str, dict[str, dict[str, str]]]:
    """Restructure CMR data into a dictionary with 'concept-id' as the key."""
    return {dataset["meta"]["concept-id"]: dataset for dataset in cmr_data}


def remove_unauthorized_classifications(classifications: list[str]) -> list[str]:
    """Filter classifications to keep only those in the authorized list."""

    authorized_classifications = [
        "Climate Change",
        "Disasters",
        "Extreme Heat",
        "Food Availability",
        "Health & Air Quality",
        "Human Dimensions",
        "Urban Flooding",
        "Water Availability",
    ]

    return [cls for cls in classifications if cls in authorized_classifications]


def update_cmr_with_classifications(
    inferences: list[dict[str, dict]],
    cmr_dict: dict[str, dict[str, dict]],
    thresholds: dict[str, float],
) -> list[dict[str, dict]]:
    """Update CMR data with valid classifications based on inferences."""

    predicted_cmr = []

    for inference in inferences:
        classifications = process_classifications(predictions=inference["predictions"], thresholds=thresholds)
        classifications = remove_unauthorized_classifications(classifications)

        if classifications:
            cmr_dataset = cmr_dict.get(inference["concept-id"])

            if cmr_dataset:
                cmr_dataset["indicators"] = ";".join(classifications)
                predicted_cmr.append(cmr_dataset)

    return predicted_cmr


def main():
    thresholds = {
        "Not EJ": 0.80,
        "Climate Change": 0.95,
        "Disasters": 0.80,
        "Extreme Heat": 0.50,
        "Food Availability": 0.80,
        "Health & Air Quality": 0.90,
        "Human Dimensions": 0.80,
        "Urban Flooding": 0.50,
        "Water Availability": 0.80,
    }

    inferences = load_json_file("alpha-1.3-wise-vortex-42-predictions.json")
    cmr = load_json_file("cmr_collections_umm_20240807_142146.json")

    cmr_dict = create_cmr_dict(cmr)

    predicted_cmr = update_cmr_with_classifications(inferences=inferences, cmr_dict=cmr_dict, thresholds=thresholds)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"ej_dump_{timestamp}.json"

    save_to_json(predicted_cmr, file_name)
    print(f"Saved to {file_name}")


if __name__ == "__main__":
    main()

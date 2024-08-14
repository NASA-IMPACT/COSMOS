"""
inferences are supplied by the classification model. the contact point is Bishwas
cmr is supplied by running https://github.com/NASA-IMPACT/llm-app-EJ-classifier/blob/develop/scripts/data_processing/download_cmr.py
move to the serve like this: scp scripts/ej/ej_dump_20240814_143036.json  sde:/home/ec2-user/sde_indexing_helper/backups/
"""

import json
from datetime import datetime

inferences = json.load(open("cmr-inference.json"))
cmr = json.load(open("cmr_collections_umm_20240807_142146.json"))


def process_classifications(data: dict[str, any], threshold: float = 0.5) -> dict[str, any]:
    """
    Takes a classification dict as input and processes them as follows:
    1. If 'Not EJ' is the highest scoring prediction, it returns 'Not EJ' as the only classification.
    2. If 'Not EJ' is not the highest, it filters the classifications based on the provided threshold, excluding Not EJ.
    3. If no classifications pass the threshold, it defaults to 'EJ'.
    """
    predictions = data["predictions"]

    # Sort predictions by score in descending order and get the highest
    highest_prediction = sorted(predictions, key=lambda x: x["score"], reverse=True)[0]

    # Determine classifications based on the conditions
    if highest_prediction["label"] == "Not EJ":
        classifications = ["Not EJ"]
    else:
        classifications = [
            pred["label"] for pred in predictions if pred["score"] >= threshold and pred["label"] != "Not EJ"
        ]
        if not classifications:
            classifications = ["EJ"]

    return classifications


# restructure cmr dump to be a dictionary with concept-id as key
cmr_dict = {dataset["meta"]["concept-id"]: dataset for dataset in cmr}

predicted_cmr = []

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


for inference in inferences:
    classifications = process_classifications(inference)
    if classifications == ["Not EJ"]:
        continue

    # Filter classifications to keep only those in the authorized list
    classifications = [cls for cls in classifications if cls in authorized_classifications]

    cmr_dataset = cmr_dict.get(inference["concept-id"])
    if cmr_dataset:
        cmr_dataset["indicators"] = ";".join(classifications)
        predicted_cmr.append(cmr_dataset)

timestamp: str = datetime.now().strftime("%Y%m%d_%H%M%S")
file_name: str = f"ej_dump_{timestamp}.json"

json.dump(predicted_cmr, open(file_name, "w"), indent=2)

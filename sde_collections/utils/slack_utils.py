import requests
from django.conf import settings

from ..models.collection_choice_fields import WorkflowStatusChoices

SLACK_ID_MAPPING = {
    "Carson Davis": "@UESJLQXH6",
    "Bishwas Praveen": "@U05QZUF182J",
    "Xiang Li": "@U03PPLNDZA7",
    "Shravan Vishwanathan": "@U056B4HMGEP",
    "Advait Yogaonkar": "@U06L5SKQ5QA",
    "Emily Foshee": "@UPKDARB9P",
    "Ashish Acharya": "@UC97PNAF6",
    "channel": "!here",
}


STATUS_CHANGE_NOTIFICATIONS = {
    (WorkflowStatusChoices.RESEARCH_IN_PROGRESS, WorkflowStatusChoices.READY_FOR_ENGINEERING): {
        "message": "Research on {name} is complete. Ready for engineering! :rocket:",
        "tags": [
            SLACK_ID_MAPPING["Xiang Li"],
            SLACK_ID_MAPPING["Shravan Vishwanathan"],
            SLACK_ID_MAPPING["Advait Yogaonkar"],
        ],
    },
    (WorkflowStatusChoices.ENGINEERING_IN_PROGRESS, WorkflowStatusChoices.READY_FOR_CURATION): {
        "message": "Engineering on {name} is complete. Ready for curation! :mag:",
        "tags": [SLACK_ID_MAPPING["Emily Foshee"]],
    },
    (WorkflowStatusChoices.CURATION_IN_PROGRESS, WorkflowStatusChoices.CURATED): {
        "message": "Curation on {name} is complete. It's now curated! :checkered_flag:",
        "tags": [
            SLACK_ID_MAPPING["Carson Davis"],
            SLACK_ID_MAPPING["Bishwas Praveen"],
            SLACK_ID_MAPPING["Ashish Acharya"],
        ],
    },
    (WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED, WorkflowStatusChoices.SECRET_DEPLOYMENT_FAILED): {
        "message": "Alert: Secret deployment of {name} has failed! :warning:",
        "tags": [
            SLACK_ID_MAPPING["Carson Davis"],
            SLACK_ID_MAPPING["Bishwas Praveen"],
            SLACK_ID_MAPPING["Ashish Acharya"],
        ],
    },
    (WorkflowStatusChoices.SECRET_DEPLOYMENT_STARTED, WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK): {
        "message": "Indexing of {name} on Secret Prod completed successfully. Ready for LRM QC! :clipboard:",
        "tags": [SLACK_ID_MAPPING["Shravan Vishwanathan"], SLACK_ID_MAPPING["Advait Yogaonkar"]],
    },
    (WorkflowStatusChoices.READY_FOR_LRM_QUALITY_CHECK, WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK): {
        "message": "LRM QC passed for {name}. Ready for final quality check! :white_check_mark:",
        "tags": [SLACK_ID_MAPPING["Emily Foshee"]],
    },
    (WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK, WorkflowStatusChoices.QUALITY_CHECK_FAILED): {
        "message": "Quality check on {name} has failed. Changes needed! :x:",
        "tags": [
            SLACK_ID_MAPPING["Xiang Li"],
            SLACK_ID_MAPPING["Shravan Vishwanathan"],
            SLACK_ID_MAPPING["Advait Yogaonkar"],
        ],
    },
    (WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK, WorkflowStatusChoices.QUALITY_CHECK_PERFECT): {
        "message": "{name} has passed all quality checks and is ready for public production! :white_check_mark:",
        "tags": [
            SLACK_ID_MAPPING["Carson Davis"],
            SLACK_ID_MAPPING["Bishwas Praveen"],
            SLACK_ID_MAPPING["Ashish Acharya"],
        ],
    },
    (WorkflowStatusChoices.READY_FOR_FINAL_QUALITY_CHECK, WorkflowStatusChoices.QUALITY_CHECK_MINOR): {
        "message": "{name} has passed all quality checks and is ready for public production! :white_check_mark:",
        "tags": [
            SLACK_ID_MAPPING["Carson Davis"],
            SLACK_ID_MAPPING["Bishwas Praveen"],
            SLACK_ID_MAPPING["Ashish Acharya"],
        ],
    },
    (WorkflowStatusChoices.QUALITY_CHECK_PERFECT, WorkflowStatusChoices.PROD_PERFECT): {
        "message": "{name} is now live on Public Prod! Congrats team! :sparkles:",
        "tags": [SLACK_ID_MAPPING["channel"]],
    },
    (WorkflowStatusChoices.QUALITY_CHECK_MINOR, WorkflowStatusChoices.PROD_MINOR): {
        "message": "{name} is now live on Public Prod! Congrats team! :sparkles:",
        "tags": [SLACK_ID_MAPPING["channel"]],
    },
}


def format_slack_message(name, details, collection_id):
    message_template = details["message"]
    tags = " ".join([f"<{user}>" for user in details["tags"]])
    link = f"https://sde-indexing-helper.nasa-impact.net/{collection_id}/"
    linked_name = f"<{link}|{name}>"
    return tags + " " + message_template.format(name=linked_name)


def send_slack_message(message):
    webhook_url = settings.SLACK_WEBHOOK_URL
    payload = {"text": message}
    response = requests.post(webhook_url, json=payload)
    if response.status_code != 200:
        raise ValueError(
            f"Request to Slack returned an error {response.status_code}, the response is:\n{response.text}"
        )

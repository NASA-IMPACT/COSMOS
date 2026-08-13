"""Read a WEB_COSMOS run's outcome from S3 — never ecs.describe_tasks.

The indexer writes index_runs/{config_folder}/{run_id}/status.json last and
unconditionally, including on failure; on test runs it also writes validation.json
(the WORKFLOW.md steps 22–25 count/title QC report, produced indexer-side because
only it holds AOSS credentials).
"""

import json

from botocore.exceptions import ClientError
from django.conf import settings

from ..utils.aws import get_boto3_session

_MISSING_KEY_CODES = {"NoSuchKey", "404"}


def run_prefix(config_folder: str, run_id: str) -> str:
    return f"index_runs/{config_folder}/{run_id}"


def _fetch_json(key: str):
    s3 = get_boto3_session().client("s3")
    try:
        obj = s3.get_object(Bucket=settings.SDE_INDEX_BUCKET, Key=key)
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in _MISSING_KEY_CODES:
            return None
        raise
    return json.loads(obj["Body"].read())


def fetch_run_status(config_folder: str, run_id: str):
    """status.json as a dict, or None while the run is still in flight."""
    return _fetch_json(f"{run_prefix(config_folder, run_id)}/status.json")


def fetch_validation_report(config_folder: str, run_id: str):
    """validation.json (test runs only), or None if absent."""
    return _fetch_json(f"{run_prefix(config_folder, run_id)}/validation.json")

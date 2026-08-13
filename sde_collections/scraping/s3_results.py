"""Read crawl results from the crawler's S3 bucket.

Key layout mirrors sde-crawl4ai-scraper-v1/sde_crawler/job.py::s3_keys_for_collection —
do not reinvent it. The crawler writes no status file: the failures summary is written
only at the end of a completed run, so a *fresh* summary is the completion marker.
S3 objects persist between runs, which is why every check must be filtered against the
latest ScrapeDispatch.dispatched_at — without it, any re-dispatch would instantly
"complete" against the previous run's output.
"""

import json

from botocore.exceptions import ClientError
from django.conf import settings

from ..utils.aws import get_boto3_session

_MISSING_KEY_CODES = {"NoSuchKey", "404"}


def s3_keys_for_collection(collection_id: str) -> dict[str, str]:
    return {
        "documents": f"scraped_collections/{collection_id}.json",
        "failures": f"failure_logs/{collection_id}_failures.jsonl",
        "summary": f"failure_logs/{collection_id}_failures_summary.json",
    }


def _get_object(key: str):
    s3 = get_boto3_session().client("s3")
    return s3.get_object(Bucket=settings.SDE_S3_BUCKET, Key=key)


def fetch_summary(collection_id: str):
    """Return (summary_dict, last_modified) or None if no summary object exists."""
    try:
        obj = _get_object(s3_keys_for_collection(collection_id)["summary"])
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") in _MISSING_KEY_CODES:
            return None
        raise
    return json.loads(obj["Body"].read()), obj["LastModified"]


def fetch_documents(collection_id: str) -> list[dict]:
    """The scraped documents array; each item has exactly seven fields:
    {url, title, full_text, content_type, seed, host, depth}."""
    obj = _get_object(s3_keys_for_collection(collection_id)["documents"])
    return json.loads(obj["Body"].read())


def results_ready(collection_id: str, dispatched_at):
    """Return the summary dict if a run completed *after* dispatched_at, else None.

    A summary whose LastModified predates the dispatch belongs to a previous run and is
    treated as absent. dispatched_at=None (no dispatch recorded) accepts any summary —
    that path is reserved for explicit manual ingest.
    """
    found = fetch_summary(collection_id)
    if found is None:
        return None
    summary, last_modified = found
    if dispatched_at is not None and last_modified <= dispatched_at:
        return None
    return summary

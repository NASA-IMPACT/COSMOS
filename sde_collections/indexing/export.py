"""Export a collection's curated set to the indexing hand-off bucket.

Layout (fixed by the built WEB_COSMOS indexer — do not re-negotiate silently):

  s3://{SDE_INDEX_BUCKET}/curated_collections/{config_folder}/{run_id}/
      documents.jsonl
      manifest.json      <- written LAST = "export complete"

COSMOS exports raw curated fields only. The indexer mints id/version itself
(web/web_processor.py is the sole owner of identity), verifies the JSONL line count
against manifest.document_count (skipping deletions on mismatch), and drops fields not
in its allow-list (tdamm_tag is exported but not indexed).
"""

import json
import tempfile

from django.conf import settings
from django.utils import timezone

from ..models.collection_choice_fields import Divisions, DocumentTypes
from ..utils.aws import get_boto3_session

SCHEMA_VERSION = 1


def export_prefix(config_folder: str, run_id: str) -> str:
    return f"curated_collections/{config_folder}/{run_id}"


def _label(choices_cls, value):
    """Resolve a nullable choices int to its label; None stays None."""
    if value is None:
        return None
    return choices_cls(value).label


def _document_line(curated_url, collection_division, collection_document_type) -> dict:
    """One JSONL line. Per-URL division/document_type only when they differ from the
    collection default (the indexer broadcasts manifest values for missing fields)."""
    line = {
        "url": curated_url.url,
        # Resolved at export time: manual/generated title wins over the scraped one.
        "title": curated_url.generated_title or curated_url.scraped_title,
        "full_text": curated_url.scraped_text,
        "is_metadata_viewer": False,
    }

    if curated_url.document_type is not None and curated_url.document_type != collection_document_type:
        line["document_type"] = _label(DocumentTypes, curated_url.document_type)
    if curated_url.division is not None and curated_url.division != collection_division:
        line["division"] = _label(Divisions, curated_url.division)

    # tdamm_tag is a PairedFieldDescriptor (manual over ML), not a column — instance
    # access only. Exported but not indexed (excluded from the indexer's version hash).
    tdamm = curated_url.tdamm_tag
    if tdamm:
        line["tdamm_tag"] = list(tdamm)

    return line


def export_curated_to_s3(collection, target: str, run_id: str) -> int:
    """Stream the curated set to S3; manifest last. Returns the exact document count."""
    from ..models.delta_url import CuratedUrl

    s3 = get_boto3_session().client("s3")
    bucket = settings.SDE_INDEX_BUCKET
    if not bucket:
        raise ValueError("SDE_INDEX_BUCKET is not configured — cannot export")
    prefix = export_prefix(collection.config_folder, run_id)

    # excluded is a queryset annotation, not a field — filtering it out here is what
    # keeps curator exclusions from being published.
    curated = CuratedUrl.objects.filter(collection=collection).exclude(excluded=True).iterator()

    count = 0
    # Spooled to disk: a crawled collection can be far larger than task memory.
    with tempfile.TemporaryFile() as body:
        for curated_url in curated:
            line = _document_line(curated_url, collection.division, collection.document_type)
            body.write(json.dumps(line, ensure_ascii=False).encode("utf-8") + b"\n")
            count += 1
        body.seek(0)
        s3.upload_fileobj(body, bucket, f"{prefix}/documents.jsonl")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "collection_key": collection.config_folder,
        "collection_name": collection.name,
        "division": _label(Divisions, collection.division),
        "document_type": _label(DocumentTypes, collection.document_type),
        "target": target,
        "document_count": count,  # the indexer verifies line count against this — must be exact
        "exported_at": timezone.now().isoformat(),
        "cosmos_workflow_status": collection.workflow_status,
    }
    # Written LAST: its presence is the "export complete" signal the indexer trusts.
    s3.put_object(
        Bucket=bucket,
        Key=f"{prefix}/manifest.json",
        Body=json.dumps(manifest).encode("utf-8"),
        ContentType="application/json",
    )
    return count

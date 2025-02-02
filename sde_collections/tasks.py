import json
import os
import shutil

import boto3
from celery import group
from django.apps import apps
from django.conf import settings
from django.core import management
from django.core.management.commands import loaddata
from django.db import transaction

from config import celery_app
from sde_collections.models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)

from .models.delta_url import DumpUrl
from .sinequa_api import Api
from .utils.github_helper import GitHubHandler


def _get_data_to_import(collection, server_name):
    # ignore these because they are API collections and don't have URLs
    ignore_collections = [
        "/SMD/ASTRO_NAVO_HEASARC/",
        "/SMD/CASEI_Campaign/",
        "/SMD/CASEI_Deployment/",
        "/SMD/CASEI_Instrument/",
        "/SMD/CASEI_Platform/",
        "/SMD/CMR_API/",
        "/SMD/PDS_API_Legacy_All/",
    ]

    data_to_import = []
    api = Api(server_name=server_name)
    page = 1
    while True:
        print(f"Getting page: {page}")
        response = api.query(page=page, collection_config_folder=collection.config_folder)
        if response["cursorRowCount"] == 0:
            break

        for record in response.get("records", []):
            full_collection_name = record.get("collection")[0]
            if full_collection_name in ignore_collections:
                continue

            url = record.get("download_url")
            title = record.get("title", "")
            collection_pk = collection.pk

            if not url:
                continue

            augmented_data = {
                "model": "sde_collections.url",
                "fields": {
                    "collection": collection_pk,
                    "url": url,
                    "scraped_title": title,
                },
            }

            data_to_import.append(augmented_data)
        page += 1
    return data_to_import


@celery_app.task(soft_time_limit=10000)
def import_candidate_urls_from_api(server_name="test", collection_ids=[]):
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)
    Collection = apps.get_model("sde_collections", "Collection")

    collections = Collection.objects.filter(id__in=collection_ids)

    for collection in collections:
        urls_file = f"{TEMP_FOLDER_NAME}/{collection.config_folder}.json"

        print("Getting responses from API")
        data_to_import = _get_data_to_import(server_name=server_name, collection=collection)
        print(f"Got {len(data_to_import)} records for {collection.config_folder}")

        print("Dumping django fixture to file")
        json.dump(data_to_import, open(urls_file, "w"))

        print("Deleting existing candidate URLs")
        # this sometimes takes a while
        collection.candidate_urls.all().delete()

        print("Loading fixture; this may take a while")
        # subprocess.call(f'python manage.py loaddata "{urls_file}"', shell=True)
        management.call_command(loaddata.Command(), urls_file)

        print("Applying existing patterns; this may take a while")
        collection.apply_all_patterns()

        if collection.workflow_status == WorkflowStatusChoices.READY_FOR_ENGINEERING:
            collection.workflow_status = WorkflowStatusChoices.ENGINEERING_IN_PROGRESS
            collection.save()

        # Finally set the status to READY_FOR_CURATION
        collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
        collection.save()

    print("Deleting temp files")
    shutil.rmtree(TEMP_FOLDER_NAME)


@celery_app.task()
def push_to_github_task(collection_ids):
    Collection = apps.get_model("sde_collections", "Collection")

    collections = Collection.objects.filter(id__in=collection_ids)
    github_handler = GitHubHandler(collections)
    github_handler.push_to_github()


@celery_app.task()
def sync_with_production_webapp():
    Collection = apps.get_model("sde_collections", "Collection")

    for collection in Collection.objects.all():
        collection.sync_with_production_webapp()


@celery_app.task()
def pull_latest_collection_metadata_from_github():
    Collection = apps.get_model("sde_collections", "Collection")

    FILENAME = "github_collections.json"

    gh = GitHubHandler(collections=Collection.objects.none())
    collections = gh.get_collections_from_github()

    json.dump(collections, open(FILENAME, "w"), indent=4)

    # Upload the file to S3
    s3_bucket_name = settings.AWS_STORAGE_BUCKET_NAME
    s3_key = FILENAME
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    s3_client.upload_file(FILENAME, s3_bucket_name, s3_key)


# @celery_app.task()
# def resolve_title_pattern(title_pattern_id):
#     TitlePattern = apps.get_model("sde_collections", "TitlePattern")
#     title_pattern = TitlePattern.objects.get(id=title_pattern_id)
#     title_pattern.apply()


@celery_app.task(name="sde_collections.tasks.resolve_title_pattern")
def resolve_title_pattern(title_pattern_id: int, delta_url_id: int) -> None:
    """Background task to resolve a title pattern for a specific URL"""
    DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
    DeltaTitlePattern = apps.get_model("sde_collections", "DeltaTitlePattern")
    DeltaResolvedTitle = apps.get_model("sde_collections", "DeltaResolvedTitle")
    DeltaResolvedTitleError = apps.get_model("sde_collections", "DeltaResolvedTitleError")

    try:
        with transaction.atomic():
            # First attempt to get an existing record or create a new one
            resolution, created = DeltaResolvedTitle.objects.get_or_create(
                title_pattern_id=title_pattern_id,
                delta_url_id=delta_url_id,
                defaults={"status": DeltaResolvedTitle.Status.PROCESSING},
            )

            # If we found an existing record (created=False)
            if not created:
                resolution.status = DeltaResolvedTitle.Status.PROCESSING
                resolution.save()
                print(f"Not created for DeltaURL {delta_url_id}; Pattern ID is {title_pattern_id}")

            if DeltaResolvedTitle.objects.filter(
                delta_url_id=delta_url_id,
                created_at__gt=resolution.created_at,
                status__in=[DeltaResolvedTitle.Status.PENDING, DeltaResolvedTitle.Status.PROCESSING],
            ).exists():
                print(f"Returning for DeltaURL {delta_url_id}; Pattern ID is {title_pattern_id}")
                return

            with open("/tmp/celery_debug.log", "a") as f:
                f.write(f"PROCESSING created for DeltaURL {delta_url_id}; Pattern ID is {title_pattern_id}")

            # Get pattern and URL
            pattern = DeltaTitlePattern.objects.get(id=title_pattern_id)
            delta_url = DeltaUrl.objects.get(id=delta_url_id)

            # Generate new title
            new_title, error = pattern.generate_title_for_url(delta_url)

            if error:
                DeltaResolvedTitleError.objects.create(
                    title_pattern=pattern,
                    delta_url=delta_url,
                    error_string=str(error),
                    http_status_code=getattr(error, "status_code", None),
                )
                print(f"FAILED created for DeltaURL {delta_url_id}; Pattern ID is {title_pattern_id}")
                return

            delta_url.generated_title = new_title
            delta_url.save()

            resolution.resolved_title = new_title
            resolution.status = DeltaResolvedTitle.Status.RESOLVED
            resolution.save()

            print(f"RESOLVED created for DeltaURL {delta_url_id}; Pattern ID is {title_pattern_id}")

    except Exception as e:
        DeltaResolvedTitleError.objects.create(
            title_pattern_id=title_pattern_id, delta_url_id=delta_url_id, error_string=str(e)
        )


@celery_app.task(name="sde_collections.tasks.process_title_resolutions")
def process_title_resolutions(pattern_url_pairs: list[tuple[int, int]]) -> None:
    """Creates a group of tasks and processes them with Celery's native batching"""
    # Create a group of tasks
    tasks = [resolve_title_pattern.s(pattern_id, url_id) for pattern_id, url_id in pattern_url_pairs]
    group(tasks).apply_async()


@celery_app.task(soft_time_limit=600)
def fetch_and_replace_full_text(collection_id, server_name):
    """
    Task to fetch and replace full text and metadata for a collection.
    Handles data in batches to manage memory usage and updates appropriate statuses
    upon completion.
    """
    Collection = apps.get_model("sde_collections", "Collection")

    collection = Collection.objects.get(id=collection_id)
    api = Api(server_name)

    initial_workflow_status = collection.workflow_status
    initial_reindexing_status = collection.reindexing_status

    # Step 1: Delete existing DumpUrl entries
    deleted_count, _ = DumpUrl.objects.filter(collection=collection).delete()
    print(f"Deleted {deleted_count} old records.")

    try:
        # Step 2: Process data in batches
        total_processed = 0
        for batch in api.get_full_texts(collection.config_folder):
            with transaction.atomic():
                DumpUrl.objects.bulk_create(
                    [
                        DumpUrl(
                            url=record["url"],
                            collection=collection,
                            scraped_text=record["full_text"],
                            scraped_title=record["title"],
                        )
                        for record in batch
                    ]
                )
            total_processed += len(batch)
            print(f"Processed batch of {len(batch)} records. Total: {total_processed}")

        # Step 3: Migrate dump URLs to delta URLs
        collection.migrate_dump_to_delta()

        # Step 4: Update statuses if needed
        collection.refresh_from_db()

        # Check workflow status transition
        pre_workflow_statuses = [
            WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
            WorkflowStatusChoices.READY_FOR_ENGINEERING,
            WorkflowStatusChoices.ENGINEERING_IN_PROGRESS,
            WorkflowStatusChoices.INDEXING_FINISHED_ON_DEV,
        ]
        if initial_workflow_status in pre_workflow_statuses:
            collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
            collection.save()

        # Check reindexing status transition
        if initial_reindexing_status == ReindexingStatusChoices.REINDEXING_FINISHED_ON_DEV:
            collection.reindexing_status = ReindexingStatusChoices.REINDEXING_READY_FOR_CURATION
            collection.save()

        return f"Successfully processed {total_processed} records and updated the database."

    except Exception as e:
        print(f"Error processing records: {str(e)}")
        raise

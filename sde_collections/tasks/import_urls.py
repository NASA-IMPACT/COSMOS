import json
import os
import shutil

from django.apps import apps
from django.core import management
from django.core.management.commands import loaddata
from django.db import transaction

from config import celery_app

from ..models.collection_choice_fields import (
    ReindexingStatusChoices,
    WorkflowStatusChoices,
)
from ..models.delta_url import DumpUrl
from ..sinequa_api import Api


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
        if collection.workflow_status == initial_workflow_status:
            collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
            collection.save()

        if collection.reindexing_status == initial_reindexing_status:
            collection.reindexing_status = ReindexingStatusChoices.REINDEXING_COMPLETE
            collection.save()

    except Exception as e:
        # Handle any errors and update status accordingly
        collection.refresh_from_db()
        if collection.workflow_status == initial_workflow_status:
            collection.workflow_status = WorkflowStatusChoices.READY_FOR_CURATION
            collection.save()
        if collection.reindexing_status == initial_reindexing_status:
            collection.reindexing_status = ReindexingStatusChoices.REINDEXING_FAILED
            collection.save()
        raise e

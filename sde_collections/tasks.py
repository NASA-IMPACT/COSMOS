# /sde_collections/tasks.py
import csv
import json
import os
import shutil

import boto3
import numpy as np
import requests
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


@celery_app.task()
def resolve_title_pattern(title_pattern_id):
    TitlePattern = apps.get_model("sde_collections", "TitlePattern")
    title_pattern = TitlePattern.objects.get(id=title_pattern_id)
    title_pattern.apply()


@celery_app.task(soft_time_limit=600)
def fetch_full_text(collection_id, server_name):
    """Task to fetch full text and create DumpUrls only (no migration)"""
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)
    api = Api(server_name)

    # Step 1: Delete existing DumpUrl entries
    deleted_count, _ = DumpUrl.objects.filter(collection=collection).delete()
    print(f"Deleted {deleted_count} old records.")
    try:
        total_server_count = api.get_total_count(collection.config_folder)
        print(f"Total records on the server: {total_server_count}")

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

        # Step 3: Check if classification is needed and queue if necessary
        collection.queue_necessary_classifications()

        return f"Successfully processed {total_processed} records."
    except Exception as e:
        print(f"Error processing records: {str(e)}")
        raise


@celery_app.task()
def migrate_dump_to_delta_and_handle_status_transistions(collection_id):
    """Task to migrate DumpUrls to DeltaUrls after classification is complete"""
    Collection = apps.get_model("sde_collections", "Collection")
    collection = Collection.objects.get(id=collection_id)

    initial_workflow_status = collection.workflow_status
    initial_reindexing_status = collection.reindexing_status

    # Migrate dump URLs to delta URLs
    collection.migrate_dump_to_delta()

    # Update statuses if needed
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

    return f"Successfully migrated DumpUrls to DeltaUrls for collection {collection.name}."


@celery_app.task(name="generate_metrics")
def generate_metrics(task_id):
    """
    Asynchronously generate metrics and save to a downloadable file
    """
    try:
        # Generate a file path in the media directory
        metrics_dir = os.path.join(settings.MEDIA_ROOT, "metrics")
        os.makedirs(metrics_dir, exist_ok=True)

        # Clean up old metrics files
        for filename in os.listdir(metrics_dir):
            if filename.startswith("metrics_") and (filename.endswith(".csv") or filename.endswith(".tmp")):
                # Skip the current task's files
                if not filename.startswith(f"metrics_{task_id}"):
                    file_path = os.path.join(metrics_dir, filename)
                    try:
                        os.remove(file_path)
                        print(f"Deleted old metrics file: {filename}")
                    except Exception as e:
                        print(f"Failed to delete {filename}: {str(e)}")

        # Use a temporary file during generation
        temp_file_path = os.path.join(metrics_dir, f"metrics_{task_id}.tmp")
        final_file_path = os.path.join(metrics_dir, f"metrics_{task_id}.csv")

        # Initialize common variables
        divArr = [
            "/Astrophysics/",
            "/Biological and Physical Sciences/",
            "/Earth Science/",
            "/Heliophysics/",
            "/Planetary Science/",
        ]
        docArr = ["Data", "Images", "Documentation", "Software and Tools", "Missions and Instruments"]

        url = "https://sciencediscoveryengine.nasa.gov/api/v1/search.query"

        # Create a temporary buffer for CSV data
        with open(temp_file_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # SECTION 1: DOCUMENT COUNT METRICS
            writer.writerow(["SECTION 1: DOCUMENT COUNT BY DIVISION AND DOCUMENT TYPE"])
            writer.writerow([])

            # Initialize document count array
            recCounter = np.zeros((6, 5))

            # Process documents through API
            pageCount = 1
            pageSize = 1000

            print("Fetching document count metrics...")

            while True:
                payload = {
                    "app": "nasa-sba-smd",
                    "query": {
                        "name": "query-smd-primary",
                        "page": pageCount,
                        "pageSize": pageSize,
                        "scope": "All",
                        "advanced": {},
                    },
                }

                print(f"Processing page {pageCount} for document count")
                response_data = requests.post(url, headers={}, json=payload, verify=False).json()

                num_records = len(response_data.get("records", []))
                if num_records == 0:
                    break

                for record in response_data["records"]:
                    if "sourcestr56" in record:
                        # Extract division and document type
                        division = record.get("treepath", [""])[0]
                        doctype = record["sourcestr56"]

                        # Update counters
                        for j in range(0, len(docArr)):
                            for k in range(0, len(divArr)):
                                if doctype == docArr[j]:
                                    if divArr[k] in division:
                                        recCounter[k, j] += 1
                                        recCounter[5, j] += 1

                pageCount += 1

            # Write document count metrics
            writer.writerow(["Division", "Document Type", "Count"])

            # Add All Divisions data
            writer.writerow(["All Divisions", "Data", str(int(recCounter[5, 0]))])
            writer.writerow(["All Divisions", "Images", str(int(recCounter[5, 1]))])
            writer.writerow(["All Divisions", "Documentation", str(int(recCounter[5, 2]))])
            writer.writerow(["All Divisions", "Software and Tools", str(int(recCounter[5, 3]))])
            writer.writerow(["All Divisions", "Missions and Instruments", str(int(recCounter[5, 4]))])
            writer.writerow(["All Divisions", "Total", str(int(np.sum(recCounter[5, :])))])

            # Add data for each division
            division_names = [
                "Astrophysics",
                "Biological and Physical Sciences",
                "Earth Science",
                "Heliophysics",
                "Planetary Science",
            ]
            for i, div_name in enumerate(division_names):
                writer.writerow([div_name, "Data", str(int(recCounter[i, 0]))])
                writer.writerow([div_name, "Images", str(int(recCounter[i, 1]))])
                writer.writerow([div_name, "Documentation", str(int(recCounter[i, 2]))])
                writer.writerow([div_name, "Software and Tools", str(int(recCounter[i, 3]))])
                writer.writerow([div_name, "Missions and Instruments", str(int(recCounter[i, 4]))])
                writer.writerow([div_name, "Total", str(int(np.sum(recCounter[i, :])))])

            # SECTION 2: SOURCES COUNT
            writer.writerow([])
            writer.writerow(["SECTION 2: SOURCES COUNT BY DIVISION"])
            writer.writerow([])

            # Initialize sources and divisions lists
            sources = []
            divs = []

            # Reset page counter for new query
            pageCount = 1

            print("Fetching sources count metrics...")

            while True:
                payload = {
                    "app": "nasa-sba-smd",
                    "query": {
                        "name": "query-smd-primary",
                        "page": pageCount,
                        "pageSize": pageSize,
                        "scope": "All",
                        "advanced": {},
                    },
                }

                print(f"Processing page {pageCount} for sources count")
                response_data = requests.post(url, headers={}, json=payload, verify=False).json()

                num_records = len(response_data.get("records", []))
                if num_records == 0:
                    break

                for record in response_data["records"]:
                    if "sourcestr56" in record:
                        source_name = record.get("collection", [""])[0]
                        division = record.get("treepath", [""])[0]

                        if source_name not in sources:
                            sources.append(source_name)
                            divs.append(division)

                pageCount += 1

            # Count sources by division
            division_counts = {div: 0 for div in divArr}
            total_count = len(sources)

            for i, div_path in enumerate(divs):
                for div in divArr:
                    if div in div_path:
                        division_counts[div] += 1

            # Write sources count metrics
            writer.writerow(["Division", "Count"])

            for div in divArr:
                writer.writerow([div.strip("/"), str(division_counts[div])])

            writer.writerow(["Total", str(total_count)])

            # SECTION 3: DOCUMENTS BY SOURCE
            writer.writerow([])
            writer.writerow(["SECTION 3: DOCUMENTS BY SOURCE"])
            writer.writerow([])

            # List of new sources to track
            new_sources = [
                "AIM: Aeronomy of Ice in the Mesosphere",
                "ASDC: Atmospheric Science Data Center",
                "G-LiHT",
                "GENESIS: Global Environmental & Earth Science Information System",
                "HyTES: Hyperspectral Thermal Emission Spectrometer",
                "IBM-NASA Prithvi Models Family",
                "COMET ASTEROID TELESCOPIC CATALOG HUNTER",
                "Escape and Plasma Acceleration and Dynamics Explorers (ESCAPADE)",
                "Extreme Ultraviolet Variability Experiment (EVE)",
                "Crustal Dynamics Data Information System",
                "Aura Atmospheric Chemistry",
                "LDOPE: Land Data Operational Products Evaluation",
                "CPL: Cloud Physics Lidar",
                "Direct Readout Laboratory",
                "Center for Near Earth Object Studies (CNEOS)",
            ]

            # Initialize counter array for source documents
            nsCounter = np.zeros((len(new_sources), 5, 5))

            # Reset page counter for new query
            pageCount = 1

            print("Fetching source documents metrics...")

            while True:
                payload = {
                    "app": "nasa-sba-smd",
                    "query": {
                        "name": "query-smd-primary",
                        "page": pageCount,
                        "pageSize": pageSize,
                        "scope": "All",
                        "advanced": {},
                    },
                }

                print(f"Processing page {pageCount} for source documents")
                response_data = requests.post(url, headers={}, json=payload, verify=False).json()

                num_records = len(response_data.get("records", []))
                if num_records == 0:
                    break

                for record in response_data["records"]:
                    if "sourcestr56" in record:
                        source_name = record.get("treepath", [""])[0]
                        division = record.get("treepath", [""])[0]
                        doc_type = record.get("sourcestr56", "")

                        for n, new_source in enumerate(new_sources):
                            if new_source in source_name:
                                for j, doc in enumerate(docArr):
                                    if doc_type == doc:
                                        for k, div in enumerate(divArr):
                                            if div in division:
                                                nsCounter[n, k, j] += 1

                pageCount += 1

            # Write source documents metrics
            for n, source in enumerate(new_sources):
                total_source_docs = np.sum(nsCounter[n, :, :])
                writer.writerow([f"Source: {source}"])
                writer.writerow(["The total number of new documents:", str(int(total_source_docs))])

                for j, doc_type in enumerate(docArr):
                    doc_count = np.sum(nsCounter[n, :, j])
                    writer.writerow([f"The total number of new {doc_type.lower()} documents:", str(int(doc_count))])
                writer.writerow([])

            writer.writerow(["DIVISION BREAKDOWN"])
            writer.writerow([])

            for d, division in enumerate(divArr):
                div_name = division.strip("/")
                total_docs = np.sum(nsCounter[:, d, :])
                writer.writerow([f"Division: {div_name}"])
                writer.writerow(["The total number of new documents:", str(int(total_docs))])

                for t, doc_type in enumerate(docArr):
                    doc_count = np.sum(nsCounter[:, d, t])
                    writer.writerow([f"The total number of new {docArr[t].lower()} documents:", str(int(doc_count))])
                writer.writerow([])

            total_overall = np.sum(nsCounter[:, :, :])
            writer.writerow(["All Divisions"])
            writer.writerow(["The total number of new documents:", str(int(total_overall))])

            for t, doc_type in enumerate(docArr):
                total_doc_type = np.sum(nsCounter[:, :, t])
                writer.writerow([f"The total number of new {docArr[t].lower()} documents:", str(int(total_doc_type))])

        # Move the file to its final location when completed
        shutil.move(temp_file_path, final_file_path)

        print(f"Metrics generation complete. File saved to {final_file_path}")
        return True

    except Exception as e:
        print(f"Error in generate_metrics: {str(e)}")
        return False

import json
import os
import shutil
import subprocess
import zipfile

import boto3
import botocore
from django.conf import settings
from django.core import management
from django.core.management.commands import loaddata
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from config import celery_app
from scraper.scraper.spiders.base_spider import spider_factory

from .models import CandidateURL, Collection
from .sinequa_api import Api


@celery_app.task()
def generate_candidate_urls_async(config_folder):
    """Generate candidate urls using celery."""
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_factory(config_folder))
    process.start()


@celery_app.task()
def import_candidate_urls_task(collection_ids=[], config_folder_names=[]):
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)

    if collection_ids:
        collections = Collection.objects.filter(id__in=collection_ids)
    elif config_folder_names:
        collections = Collection.objects.filter(config_folder__in=config_folder_names)
    else:
        collections = Collection.objects.all()

    for collection in collections:
        s3_file_path = f"scraped_urls/{collection.config_folder}.zip"
        zip_file_name = f"{TEMP_FOLDER_NAME}/{collection.config_folder}.zip"
        json_folder_name = f"{os.path.splitext(zip_file_name)[0]}"
        urls_file = f"{json_folder_name}/urls.json"
        try:
            s3.download_file(
                settings.AWS_STORAGE_BUCKET_NAME,
                s3_file_path,
                zip_file_name,
            )
            with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
                zip_ref.extractall(json_folder_name)
        except botocore.exceptions.ClientError:
            continue
        collection.candidate_urls.all().delete()

        print(f"Importing {collection.config_folder}")

        data = json.load(open(urls_file))
        augmented_data = [
            {
                "model": "sde_collections.candidateurl",
                "fields": {
                    "collection": collection.pk,
                    "url": item["url"],
                    "scraped_title": item["scraped_title"],
                },
            }
            for item in data
        ]

        json.dump(augmented_data, open(urls_file, "w"))

        collection.candidate_urls.all().delete()

        subprocess.run(f'python manage.py loaddata "{urls_file}"', shell=True)
        collection.apply_all_patterns()
        collection.curation_status = 2  # ready to curate
        collection.save()
    shutil.rmtree(TEMP_FOLDER_NAME)


@celery_app.task()
def import_all_candidate_urls_task():
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)

    s3_file_path = "scraped_urls_all/all_data.zip"
    zip_file_name = f"{TEMP_FOLDER_NAME}/all_data.zip"
    json_folder_name = f"{os.path.splitext(zip_file_name)[0]}"
    urls_file = f"{json_folder_name}/urls.json"

    print("Downloading zip file from S3")
    try:
        s3.download_file(
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_file_path,
            zip_file_name,
        )
        print("Unzipping")
        with zipfile.ZipFile(zip_file_name, "r") as zip_ref:
            zip_ref.extractall(json_folder_name)
    except botocore.exceptions.ClientError:
        print("error")
        return

    data = json.load(open(urls_file))
    augmented_data = []
    config_folder_to_pk_dict = dict(
        Collection.objects.all().values_list(
            "config_folder", "pk", flat=False, named=True
        )
    )
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

    print("Creating django fixture")
    for item in data:
        collection_name = item["collection"]
        if collection_name in ignore_collections:
            continue
        try:
            item_dict = {
                "model": "sde_collections.candidateurl",
                "fields": {
                    "collection": config_folder_to_pk_dict[
                        item["collection"].split("/")[2]
                    ],
                    "url": item["url"],
                    "scraped_title": item["scraped_title"],
                },
            }
        except Collection.DoesNotExist:
            continue
        augmented_data.append(item_dict)

    print("Dumping django fixture to file")
    json.dump(augmented_data, open(urls_file, "w"))

    print("Deleting existing candidate URLs")
    CandidateURL.objects.all().delete()

    print("Loading fixture; this may take a while")
    subprocess.run(f'python manage.py loaddata "{urls_file}"', shell=True)

    print("Applying existing patterns; this may take a while")
    for collection in Collection.objects.all():
        collection.apply_all_patterns()

    print("Deleting temp files")
    shutil.rmtree(TEMP_FOLDER_NAME)


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
        response = api.query(
            page=page, collection_config_folder=collection.config_folder
        )
        if response["cursorRowCount"] == 0:
            break

        for record in response.get("records", []):
            full_collection_name = record.get("collection")[0]
            if full_collection_name in ignore_collections:
                continue

            url = record.get("url1")
            title = record.get("title", "")
            collection_pk = collection.pk

            if not url:
                continue

            augmented_data = {
                "model": "sde_collections.candidateurl",
                "fields": {
                    "collection": collection_pk,
                    "url": url,
                    "scraped_title": title,
                },
            }

            data_to_import.append(augmented_data)
        page += 1
    return data_to_import


@celery_app.task()
def import_candidate_urls_from_api(server_name="test", collection_ids=[]):
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)

    collections = Collection.objects.filter(id__in=collection_ids)

    for collection in collections:
        urls_file = f"{TEMP_FOLDER_NAME}/{collection.config_folder}.json"

        print("Getting responses from API")
        data_to_import = _get_data_to_import(
            server_name=server_name, collection=collection
        )
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

    print("Deleting temp files")
    shutil.rmtree(TEMP_FOLDER_NAME)

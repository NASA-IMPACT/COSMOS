import json
import os
import shutil
import subprocess
import zipfile

import boto3
import botocore
from django.conf import settings
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from config import celery_app
from scraper.scraper.spiders.base_spider import spider_factory

from .models import Collection


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
    shutil.rmtree(TEMP_FOLDER_NAME)

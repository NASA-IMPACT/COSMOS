import os
import subprocess

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
def import_candidate_urls_task(collection_ids):
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )

    collections = Collection.objects.filter(id__in=collection_ids)

    for collection in collections:
        urls_file_name = f"{collection.config_folder}_urls.json"

        try:
            s3.download_file(
                settings.AWS_STORAGE_BUCKET_NAME,
                f"static/scraped_urls/{collection.config_folder}/urls.json",
                urls_file_name,
            )
        except botocore.exceptions.ClientError:
            return

        subprocess.run(f"python manage.py loaddata {urls_file_name}", shell=True)
        os.remove(f"{urls_file_name}")

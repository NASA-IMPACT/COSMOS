import json

import boto3
from django.apps import apps
from django.conf import settings

from config import celery_app

from ..utils.github_helper import GitHubHandler


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

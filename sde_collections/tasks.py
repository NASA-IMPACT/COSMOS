import json
import os
import shutil
import requests
import boto3
from django.apps import apps
from django.conf import settings
from django.core import management
from django.core.management.commands import loaddata
from sde_collections.models.candidate_url import CandidateURL
from config import celery_app

from .models.collection import Collection, WorkflowStatusChoices
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


@celery_app.task(soft_time_limit=10000)
def import_candidate_urls_from_api(server_name="test", collection_ids=[]):
    TEMP_FOLDER_NAME = "temp"
    os.makedirs(TEMP_FOLDER_NAME, exist_ok=True)

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
    collections = Collection.objects.filter(id__in=collection_ids)
    github_handler = GitHubHandler(collections)
    github_handler.push_to_github()


@celery_app.task()
def sync_with_production_webapp():
    for collection in Collection.objects.all():
        collection.sync_with_production_webapp()


@celery_app.task()
def pull_latest_collection_metadata_from_github():
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
'''
@celery_app.task
def fetch_and_update_full_text(collection_id):
    
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        raise Exception(f"Collection with ID {collection_id} does not exist.")
    
    url = "https://sde-lrm.nasa-impact.net/api/v1/engine.sql" #LRM_DEV Server
    sql_command = f"SELECT url1, text, title FROM sde_index WHERE collection = '/SDE/{collection.config_folder}/'"
    token = os.getenv('LRMDEV_TOKEN')


    payload = json.dumps({
        "method": "engine.sql",
        "sql": sql_command,
        "pretty": True,
        "log": False,
        "output": "json",
        "resolveIndexList": "false",
        "engines": "default"
    })
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }
    
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        records = response.json().get("Rows", [])
        for record in records:
            url, full_text, title = record
            if not url or not full_text or not title:
                continue
            # Directly update or create the entry without checking for content changes
            CandidateURL.objects.update_or_create(
                url=url,
                collection=collection,
                defaults={
                    'scraped_text': full_text,
                    'scraped_title': title
                }
            )

        return f"Processed {len(records)} records; Updated or created in database."
    else:
        raise Exception(f"Failed to fetch text: {response.status_code} {response.text}")
    '''

#You will have to have a different function for Li's server as it uses user and pw with body to login.
#If the sinequa web token is used, can user&pw be removed from the body? if yes then can integrate, but headers will b diff (auth/cookie). if lis then header1, elif lrm_dev then h2, else h3
#Fill in the tokens in the .django file

#Integrated - LRM devs and Lis separate
'''
@celery_app.task
def fetch_and_update_full_text(collection_id, server_type):
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        raise Exception(f"Collection with ID {collection_id} does not exist.")
    
    # Server-specific configurations
    server_config = get_server_config(server_type)

    # API Request Parameters
    payload = json.dumps({
        "method": "engine.sql",
        "sql": f"SELECT url1, text, title FROM sde_index WHERE collection = '/SDE/{collection.config_folder}/'",
        "pretty": True,
        "log": False,
        "output": "json",
        "resolveIndexList": "false",
        "engines": "default"
    })

    token = server_config["token"]
    url = server_config["url"]
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    # Send the request
    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        records = response.json().get("Rows", [])
        for record in records:
            url, full_text, title = record
            if not url or not full_text or not title:
                continue
            CandidateURL.objects.update_or_create(
                url=url,
                collection=collection,
                defaults={
                    'scraped_text': full_text,
                    'scraped_title': title
                }
            )
        return f"Processed {len(records)} records; Updated or created in database."
    else:
        raise Exception(f"Failed to fetch text: {response.status_code} {response.text}")


def get_server_config(server_type):
    if server_type == "LRM_DEV":
        return {
            "url": "https://sde-lrm.nasa-impact.net/api/v1/engine.sql",
            "token": os.getenv("LRMDEV_TOKEN")
        }
    elif server_type == "LIS":
        return {
            "url": "http://sde-xli.nasa-impact.net/api/v1/engine.sql",
            "token": os.getenv("LIS_TOKEN")
        }
    else:
        raise ValueError("Invalid server type.")
'''


@celery_app.task
def fetch_and_update_full_text(collection_id, server_type):
    try:
        collection = Collection.objects.get(id=collection_id)
    except Collection.DoesNotExist:
        raise Exception(f"Collection with ID {collection_id} does not exist.")

    server_config = get_server_config(server_type)
    token = server_config["token"]
    url = server_config["url"]

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    }

    payload = json.dumps({
        "method": "engine.sql",
        "sql": f"SELECT url1, text, title FROM sde_index WHERE collection = '/SDE/{collection.config_folder}/'",
        "pretty": True,
        "log": False,
        "output": "json",
        "resolveIndexList": "false",
        "engines": "default"
    })

    try:
        response = requests.post(url, headers=headers, data=payload, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
    except requests.exceptions.RequestException as e:
        raise Exception(f"API request failed: {str(e)}")

    records = response.json().get("Rows", [])
    if not records:
        return "No records found in the response."

    for record in records:
        url, full_text, title = record
        if not (url and full_text and title):
            continue 

        CandidateURL.objects.update_or_create(
            url=url,
            collection=collection,
            defaults={
                'scraped_text': full_text,
                'scraped_title': title
            }
        )

    return f"Successfully processed {len(records)} records and updated the database."

def get_server_config(server_type):
    if server_type == "LRM_DEV":
        return {
            "url": "https://sde-lrm.nasa-impact.net/api/v1/engine.sql",
            "token": os.getenv("LRMDEV_TOKEN")
        }
    elif server_type == "LIS":
        return {
            "url": "http://sde-xli.nasa-impact.net/api/v1/engine.sql",
            "token": os.getenv("LIS_TOKEN")
        }
    else:
        raise ValueError("Invalid server type.")


import json
import os
import zipfile

import boto3
import environ
from api import Api

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COLLECTIONS_TO_UPLOAD = [
    # list of collections to upload, eg: "DataPathFinder"
]

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

api = Api("test_server")

for collection in COLLECTIONS_TO_UPLOAD:
    print(f"Running SQL query for collection {collection}...")
    response = api.sql("SMD", collection)

    # TODO: save response to a csv with f'{collection}.xml' as the name
    candidate_urls = response["Rows"]
    bulk_data = [
        {
            "url": candidate_url[0],
            "scraped_title": candidate_url[1],
        }
        for candidate_url in candidate_urls
    ]

    TEMP_FOLDER_NAME = "temp"

    # Folder to create temporary files
    os.makedirs(f"{TEMP_FOLDER_NAME}/{collection}", exist_ok=True)

    # Create JSON file
    print("Creating JSON dump...")
    json_data = json.dumps(bulk_data)
    file_path = f"{TEMP_FOLDER_NAME}/{collection}/urls.json"  # Provide the desired file path
    with open(file_path, "w") as file:
        file.write(json_data)

    # Zip the JSON file
    print("Creating zip file...")
    zip_file_path = f"{TEMP_FOLDER_NAME}/{collection}.zip"  # Provide the desired zip file path
    with zipfile.ZipFile(zip_file_path, "w") as zip_file:
        zip_file.write(file_path, os.path.basename(file_path))

    # Upload the zip file to S3
    s3_bucket_name = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
    s3_key = f"scraped_urls/{collection}.zip"  # Provide the desired S3 key for the uploaded file
    s3_client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=env("DJANGO_AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=env("DJANGO_AWS_SECRET_ACCESS_KEY"),
    )
    print(f"Uploading to S3 bucket at {s3_key}...")
    s3_client.upload_file(zip_file_path, s3_bucket_name, s3_key)

    # Delete the original JSON and zip file
    print("Deleting json file and zip file...")
    os.remove(file_path)
    os.remove(zip_file_path)
    print("Success!\n")

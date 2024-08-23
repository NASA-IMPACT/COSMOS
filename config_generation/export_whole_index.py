import json
import os
import zipfile

import boto3
import environ
from api import Api

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(DEBUG=(bool, False))

environ.Env.read_env(os.path.join(BASE_DIR, ".env"))

api = Api("test_server")

response = api.sql("SMD", fetch_all=True)

candidate_urls = response["Rows"]
bulk_data = [
    {
        "url": candidate_url[0],
        "scraped_title": candidate_url[1],
        "collection": candidate_url[2],
    }
    for candidate_url in candidate_urls
]

TEMP_FOLDER_NAME = "temp"

# Folder to create temporary files
os.makedirs(f"{TEMP_FOLDER_NAME}/all_data", exist_ok=True)

# Create JSON file
json_data = json.dumps(bulk_data)
file_path = f"{TEMP_FOLDER_NAME}/all_data/urls.json"  # Provide the desired file path
with open(file_path, "w") as file:
    file.write(json_data)

# Zip the JSON file
zip_file_path = f"{TEMP_FOLDER_NAME}/all_data.zip"  # Provide the desired zip file path
with zipfile.ZipFile(zip_file_path, "w") as zip_file:
    zip_file.write(file_path, os.path.basename(file_path))

# Upload the zip file to S3
s3_bucket_name = env("DJANGO_AWS_STORAGE_BUCKET_NAME")
s3_key = "scraped_urls_all/all_data.zip"  # Provide the desired S3 key for the uploaded file
s3_client = boto3.client(
    "s3",
    region_name="us-east-1",
    aws_access_key_id=env("DJANGO_AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=env("DJANGO_AWS_SECRET_ACCESS_KEY"),
)
s3_client.upload_file(zip_file_path, s3_bucket_name, s3_key)

# Delete the original JSON and zip file
os.remove(file_path)
os.remove(zip_file_path)

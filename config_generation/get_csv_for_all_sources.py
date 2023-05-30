import json
import os
import zipfile

import boto3
import environ
from api import Api
from generate_collection_list import turned_on_remaining_webcrawlers

# Set the project base directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, ".env"))


api = Api("test_server")

dont_ingest_into_webapp = [
    "giss_datasets_and_derived_materials",
    "nasa_sea_level_change",
    "PDS_Missions_Archive_Page_Website",
    "PDS_Venus_Orbital_Data_Explorer_Website",
    "PDS_PDS4_Documents_Website",
    "PDS_Mars_Lander_Data_Website",
    "PDS_Planetary_Science_Tools_Website",
    "PDS_PDS_Documentation_Website",
    "PDS_PDS4_Local_Data_Dictionary_Tool_Website",
    "PDS_Data_Volumes_Index_Website",
    "PDS_Mars_Orbital_Data_Explorer_Website",
    "giss_publication_list",
    "nasa_carbon_monitoring_system",
    "PDS_Mars_Exploration_Program_Website",
    "PDS_PDS_Tool_Registry_Website",
    "ASTRO_NASA_Exoplanet_Archive_Documents_Website",
    "ASTRO_MAST_Documentation_Website",
    "Autoplot_Website",
    "PDS_ISIS_Website",
    "PDS_LOLA_RDR_Query_V20_Website",
    "ASTRO_Data_Reduction_Tools_Website",
    "PDS_Ring",
    "ASTRO_TAP_Search_Website",
    "PDS_Geosciences_Node_Spectral_Library_Website",
    "PDS_SPICE",
    "PDS_DIVINER_RDR_Query_V20_Website",
    "PDS_PDS4_JParser_Website",
    "PDS_Atmospheric_Escape_Chemistry_Page_Website",
    "goddard_institute_for_space_studies",
    "emac_exoplanet_modeling_and_analysis_center",
]

for collection in turned_on_remaining_webcrawlers:
    print(collection)
    BASE_URL = "https://sde-indexing-helper.nasa-impact.net"
    POST_URL = f"{BASE_URL}/api/candidate-urls/{collection}/bulk-create/"

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
    json_data = json.dumps(bulk_data)
    file_path = (
        f"{TEMP_FOLDER_NAME}/{collection}/urls.json"  # Provide the desired file path
    )
    with open(file_path, "w") as file:
        file.write(json_data)

    # Zip the JSON file
    zip_file_path = (
        f"{TEMP_FOLDER_NAME}/{collection}.zip"  # Provide the desired zip file path
    )
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
    s3_client.upload_file(zip_file_path, s3_bucket_name, s3_key)

    # Delete the original JSON and zip file
    os.remove(file_path)
    os.remove(zip_file_path)

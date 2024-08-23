"""this document compares creates a list of sources to scrape
- start with turned on sources
- remove already scraped sources
- filter anything that isn't a webcrawler
- provide a variable, turned_on_remaining_webcrawlers for import by other files
"""
import os

from db_to_xml import XmlEditor
from sources_to_scrape import (
    already_scraped_sources,
    sources_with_documents_20230605,
    turned_on_sources,
)

ROOT_PATH = "../sinequa_configs/sources/SDE/"


def create_xml_path(collection_name):
    return f"{ROOT_PATH}{collection_name}/default.xml"


def get_turned_on_sources():
    # remove sources that were just scraped
    turned_on_remaining_sources = [source for source in turned_on_sources if source not in already_scraped_sources]

    # filter all sources to only webcrawler sources
    turned_on_remaining_webcrawlers = []
    for collection_name in turned_on_remaining_sources:
        path = create_xml_path(collection_name)
        indexer = XmlEditor(path)
        if "crawler2" in indexer.get_tag_value("Connector"):
            turned_on_remaining_webcrawlers.append(collection_name)


def is_collection_crawler(collection_name):
    config = XmlEditor(create_xml_path(collection_name))
    return "crawler2" in config.get_tag_value("Connector")


def get_all_config_folder_names(folder_path=ROOT_PATH):
    """
    this returns a list of all the config folder names, not the path of the folder
    """
    # Look at each directory directly in the given folder
    folders = []
    for dir in os.listdir(folder_path):
        dir_path = os.path.join(folder_path, dir)
        if os.path.isdir(dir_path) and "default.xml" in os.listdir(dir_path):
            # Print the name of the directory
            folders.append(dir)
    return folders


def get_sources_20230605():
    """
    - empty webcrawlers
    - 5 sources that were interupted
    """
    interrupted_sources = [
        "PDS_Mission_Data_Archive_Website",
        "goddard_institute_for_space_studies",
        "ASTRO_Image_Cutouts_Website",
        "PDS_Mars_Exploration_Program_Website",
    ]
    folders = get_all_config_folder_names()
    folders = folders + interrupted_sources
    return [
        folder for folder in folders if folder not in sources_with_documents_20230605 and is_collection_crawler(folder)
    ]

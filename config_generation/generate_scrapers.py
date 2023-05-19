# this file creates new Candidate URL scraper configs
import os

from config_utilities import (
    create_config_folder_and_default,
    create_folder,
    open_xml_as_dict,
)

# from db_to_xml import convert_indexer_to_scraper


def get_or_create_folder(scraper_folder_name="scraping_configs"):
    # TODO: probably don't need this function
    """
    scraper configs are placed in their own folder above this directory
    this gets that folder path
    """

    scraper_folder_path = os.path.join(
        os.path.dirname(os.getcwd()), scraper_folder_name
    )
    # creates the folder if it doesn't already exist
    create_folder(scraper_folder_path)

    return scraper_folder_path


def get_scraper_folder(scraper_folder_name="scraping_configs"):
    """
    scraper configs are placed in their own folder above this directory
    this gets that folder path
    """

    scraper_folder_path = os.path.join(
        os.path.dirname(os.getcwd()), scraper_folder_name
    )
    # creates the folder if it doesn't already exist
    create_folder(scraper_folder_path)

    return scraper_folder_path


def generate_brand_new_scraper(
    source_name, url, scraper_template_path="xmls/scraper_template.xml"
):
    """

    Args:
        source_name (str): Collection.machine_name
        url (str): Collection.url
        scraper_template_path (str, optional): path to the template from which to generate the scraper.
          Defaults to "xmls/scraper_template.xml".
    """

    scraper = open_xml_as_dict(scraper_template_path)
    scraper["Sinequa"]["Url"] = url

    scraper_folder_path = get_scraper_folder()
    create_config_folder_and_default(scraper_folder_path, source_name, scraper)


# def generate_scraper_based_on_existing(source_name, existing_config_path):
#     existing_config_xml = get_tree(existing_config_path)
#     scraper_xml = convert_indexer_to_scraper(existing_config_xml)


# if __name__ == "__main__":
# from sources_to_scrape import kaylins_new_sources

# for source in kaylins_new_sources:
#     generate_scraper(source["source_name"], source["url"])

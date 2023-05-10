# this file creates new Candidate URL scraper configs
import os

from config_utilities import (
    create_config_folder_and_default,
    create_folder,
    open_xml_as_dict,
)


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


def generate_scraper(source_name, url, scraper_template_path="scraper_template.xml"):
    """
    this takes the scraper template and adds the url,
    then it creates an xml file named default.xml inside a folder named after the source
    """

    scraper = open_xml_as_dict(scraper_template_path)
    scraper["Sinequa"]["Url"] = url

    scraper_folder_path = get_scraper_folder()
    create_config_folder_and_default(scraper_folder_path, source_name, scraper)


if __name__ == "__main__":
    from sources_to_scrape import kaylins_new_sources

    for source in kaylins_new_sources:
        generate_scraper(source["source_name"], source["url"])

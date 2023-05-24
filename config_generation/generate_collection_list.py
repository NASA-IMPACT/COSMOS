"""this document compares creates a list of sources to scrape
- start with turned on sources
- remove already scraped sources
- filter anything that isn't a webcrawler
- provide a variable, turned_on_remaining_webcrawlers for import by other files
"""

from sources_to_scrape import turned_on_sources, already_scraped_sources

from db_to_xml import XmlEditor

ROOT_PATH = "../sinequa_configs/sources/SMD/"


def create_xml_path(collection_name):
    return f"{ROOT_PATH}{collection_name}/default.xml"


# remove sources that were just scraped
turned_on_remaining_sources = [
    source for source in turned_on_sources if source not in already_scraped_sources
]

# filter all sources to only webcrawler sources
turned_on_remaining_webcrawlers = []
for collection_name in turned_on_remaining_sources:
    path = create_xml_path(collection_name)
    indexer = XmlEditor(path)
    if "crawler2" in indexer.get_tag_value("Connector"):
        turned_on_remaining_webcrawlers.append(collection_name)

from db_to_xml import XmlEditor
from sources_to_scrape import turned_on_sources, already_scraped_sources

root_path = "/Users/cdavis/github/sde_ashish/sinequa_configs/sources/SMD/"


def remove_top_only_limitation(path):
    # this is only run on the exact sources where we want disabled, so checking
    # for and retaining previous values is not required
    indexer = XmlEditor(path)
    indexer.update_or_add_element_value("MaxToIndex", "")
    indexer.update_or_add_element_value("MaxLevel", "")
    indexer.update_or_add_element_value("MaxToCrawl", "")
    indexer._write_xml(path)


def ensure_index_of_root(path):
    # some indexers aren't getting the actual root url given in Url
    # this should directly ensure it is scraped
    indexer = XmlEditor(path)
    urls = indexer.get_tag_value("Url")
    for url in urls:
        indexer.add_url_include(url)
    indexer._write_xml(path)


# remove sources that were just scraped
remaining_sources = [
    source for source in turned_on_sources if source not in already_scraped_sources
]

# filter all sources to only webcrawler sources
webcrawlers = []
for collection_name in remaining_sources:
    path = f"{root_path}{collection_name}/default.xml"
    indexer = XmlEditor(path)

    if "crawler2" in indexer.get_tag_value("Connector"):
        webcrawlers.append(collection_name)

print(len(turned_on_sources))
print(len(webcrawlers))


# notes
# 139 total turned on sources
# 116 of which are webcrawlers

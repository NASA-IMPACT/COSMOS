from db_to_xml import XmlEditor
from generate_collection_list import turned_on_remaining_webcrawlers, create_xml_path
from sources_to_scrape import (
    remove_top_limitation_sources,
    turned_on_sources,
)

ROOT_PATH = "../sinequa_configs/sources/SMD/"


def remove_top_only_limitation(path):
    # this is only run on the exact sources we want disabled, so checking
    # for and retaining previous values is not required
    indexer = XmlEditor(path)
    indexer.update_or_add_element_value("MaxToIndex", "")
    indexer.update_or_add_element_value("MaxLevel", "")
    indexer.update_or_add_element_value("MaxToCrawl", "")
    indexer._update_config_xml(path)


def ensure_index_of_root(path):
    # some indexers aren't getting the actual root url given in Url
    # this should directly ensure it is scraped
    indexer = XmlEditor(path)
    urls = indexer.get_tag_value("Url")
    for url in urls:
        # ensure we don't double add these
        if url not in indexer.get_tag_value("UrlIndexIncluded"):
            indexer.add_url_include(url)
    indexer._update_config_xml(path)


# # undo top limitation
# for collection_name in remove_top_limitation_sources:
#     path = create_xml_path(collection_name)
#     remove_top_only_limitation(path)

# # ensure root
# for collection_name in turned_on_remaining_webcrawlers:
#     path = create_xml_path(collection_name)
#     ensure_index_of_root(path)

# format files...
for collection_name in turned_on_remaining_webcrawlers:
    path = create_xml_path(collection_name)
    indexer = XmlEditor(path)
    indexer._resave_pretty(path)


print(len(turned_on_sources))  # 139
print(len(turned_on_remaining_webcrawlers))  # 114
print(len(remove_top_limitation_sources))  # 5
print(
    len(
        [
            s
            for s in remove_top_limitation_sources
            if s in turned_on_remaining_webcrawlers
        ]
    )
)  # 5

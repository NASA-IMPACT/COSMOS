"""this file uses data from config.py to generate a command that will delete collection content from multiple indexes"""

from db_to_xml_file_based import XmlEditor

from config import (
    batch_delete_name,
    collection_list,
    engines,
    indexes_to_delete_from,
    source,
)

COMMAND_FILES_PATH = "../sinequa_configs/commands/"
DELETE_COMMAND_TEMPLATE_PATH = "xmls/delete_template.xml"

command_file = XmlEditor(DELETE_COMMAND_TEMPLATE_PATH)

command_file.update_or_add_element_value(element_name="Engines", element_value=",".join([engine for engine in engines]))
for collection in collection_list:
    for index in indexes_to_delete_from:
        sql = f"delete from {index} where collection='/{source}/{collection}/'"
        command_file.update_or_add_element_value(element_name="SQL", element_value=sql, add_duplicate=True)

file_name = f"{COMMAND_FILES_PATH}{batch_delete_name}.xml"
command_file._update_config_xml(file_name)

"""this file uses data from config.py to generate a command that will delete collection content from multiple indexes"""

from db_to_xml_file_based import XmlEditor

from config import collections_to_delete, indexes_to_delete_from, name_of_delete_file

COMMAND_FILES_PATH = "../sinequa_configs/commands/"
DELETE_COMMAND_TEMPLATE_PATH = "xmls/delete_template.xml"

command_file = XmlEditor(DELETE_COMMAND_TEMPLATE_PATH)

for collection in collections_to_delete:
    for index in indexes_to_delete_from:
        sql = f"delete from {index} where collection='{collection}'"
        command_file.update_or_add_element_value(element_name="SQL", element_value=sql, add_duplicate=True)
file_name = f"{COMMAND_FILES_PATH}{name_of_delete_file}.xml"
command_file._update_config_xml(file_name)

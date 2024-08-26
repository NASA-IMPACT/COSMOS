from config_generation.db_to_xml import XmlEditor

from ..models.collection import Collection
from ..models.collection_choice_fields import Divisions, DocumentTypes


def test_create_config_xml():
    collection = Collection(name="test", division=Divisions.EARTH_SCIENCE, document_type=DocumentTypes.DATA)
    output_xml = collection.create_config_xml()
    editor = XmlEditor(output_xml)
    assert collection.tree_root == editor.fetch_treeroot()
    assert collection.document_type == editor.fetch_document_type()

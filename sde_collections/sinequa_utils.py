import json
import xml.etree.ElementTree as ET

# import xmltodict
from django.conf import settings

SINEQUA_PATH = settings.BASE_DIR / "sinequa_configs" / "sources" / "SMD"


class Sinequa:
    def __init__(self, config_folder, *args, **kwargs):
        self.config_folder = config_folder
        self.collection_config_path = SINEQUA_PATH / self.config_folder / "default.xml"
        self.metadata = ET.parse(self.collection_config_path)
        self.root = self.metadata.getroot()

    def _add_declaration(self, config_file_path):
        declaration = """<?xml version="1.0" encoding="utf-8"?>"""
        with open(config_file_path, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(declaration.rstrip("\r\n") + "\n" + content)

    def _update_config_xml(self):
        self.metadata.write(
            SINEQUA_PATH / self.config_folder / "default.xml",
            method="html",
            encoding="utf-8",
            xml_declaration=True,
        )

        self._add_declaration(self.collection_config_path)

    def _find_treeroot_field(self, metadata):
        treeroot = metadata.find("TreeRoot")
        if treeroot is None:
            treeroot = metadata.find("treeRoot")
        return treeroot

    def fetch_treeroot(self):
        treeroot = self._find_treeroot_field(self.metadata)
        return treeroot.text

    def update_treeroot(self, treeroot_value):
        treeroot = self._find_treeroot_field(self.metadata)
        treeroot.text = treeroot_value
        self._update_config_xml()

    def fetch_document_type(self):
        DOCUMENT_TYPE_COLUMN = "sourcestr56"
        try:
            document_type_text = self.metadata.find(
                f"Mapping[Name='{DOCUMENT_TYPE_COLUMN}']/Value"
            ).text
        except AttributeError:
            return None

        # importing here to avoid circular import
        from sde_collections.models import Collection

        document_type = Collection.DocumentTypes.lookup_by_text(
            json.loads(document_type_text)
        )
        return document_type

    def update_document_type(self, document_type):
        DOCUMENT_TYPE_COLUMN = "sourcestr56"
        document_type_text = self.metadata.find(
            f"Mapping[Name='{DOCUMENT_TYPE_COLUMN}']/Value"
        )
        if not document_type_text:
            # doc_type_element = ET.SubElement(self.root, "Mapping")
            elements = ["Name", "Value", "Description", "Selection", "DefaultValue"]
            for element in elements:
                # element_tag = ET.SubElement(doc_type_element, element)
                pass

        # document_type_text.text = json.dumps(document_type)
        self._update_config_xml()

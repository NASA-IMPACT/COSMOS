import xml.etree.ElementTree as ET

from django.conf import settings

SINEQUA_PATH = settings.BASE_DIR / "sinequa_configs" / "sources" / "SMD"


class Sinequa:
    def __init__(self, config_folder, *args, **kwargs):
        self.config_folder = config_folder

    def _add_declaration(self, config_file_path):
        declaration = """<?xml version="1.0" encoding="utf-8"?>"""
        with open(config_file_path, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(declaration.rstrip("\r\n") + "\n" + content)

    def _find_treeroot_field(self, metadata):
        treeroot = metadata.find("TreeRoot")
        if treeroot is None:
            treeroot = metadata.find("treeRoot")
        return treeroot

    def fetch_treeroot(self):
        metadata = ET.parse(SINEQUA_PATH / self.config_folder / "default.xml")
        treeroot = self._find_treeroot_field(metadata)
        return treeroot.text

    def update_treeroot(self, treeroot_value):
        collection_config_path = SINEQUA_PATH / self.config_folder / "default.xml"
        metadata = ET.parse(collection_config_path)
        treeroot = self._find_treeroot_field(metadata)
        treeroot.text = treeroot_value
        metadata.write(
            SINEQUA_PATH / self.config_folder / "default.xml",
            method="html",
            encoding="utf-8",
            xml_declaration=True,
        )

        self._add_declaration(collection_config_path)

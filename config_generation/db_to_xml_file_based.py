# This file uses the previously written file-based xml handling code to supplement
# the new github-based xml code so that the job-creation pipeline will still work 
# we can remove it once we incorporate job creation into the github pipeline 
import os
import xml.etree.ElementTree as ET

from db_to_xml import XmlEditor as XmlEditorStringBased


class XmlEditor(XmlEditorStringBased):
    """
    Class is instantiated with a path to an xml.
    An internal etree is generated, and changes are made in place.
    An ouput path is given and the etree is saved to it.
    """

    def __init__(self, xml_path: str):
        self.input_path = xml_path
        self.xml_tree = self._get_tree(self.input_path)

    def _get_tree(self, xml_path) -> ET.ElementTree:
        """takes the path of an xml file and opens it as an ElementTree object"""
        return ET.parse(xml_path)

    def _add_declaration(self, output_path: str):
        """opens an existing file and adds a declaration"""
        declaration = """<?xml version="1.0" encoding="utf-8"?>"""
        with open(output_path, "r+") as f:
            content = f.read()
            f.seek(0, 0)
            f.write(declaration.rstrip("\r\n") + "\n" + content)

    def _update_config_xml(self, output_path: str):
        self.xml_tree.write(
            output_path,
            method="html",
            encoding="utf-8",
            xml_declaration=True,
        )

        self._add_declaration(output_path)
        self._resave_pretty(output_path)

    def _resave_pretty(self, output_path):
        """opens and resaves a file to reformat it"""
        import xmltodict

        with open(output_path) as f:
            xml_data = f.read()
        xml = xmltodict.parse(xml_data)
        with open(output_path, "w") as f:
            f.write(xmltodict.unparse(xml, pretty=True))

    def create_folder_if_needed(self, folder_path: str):
        """
        sinequa configs are source_name/collection_name/default.xml
        this function helps make the collection_name folder
        folder path is a full exact path ending in a potential collection_name folder
        """

        try:
            os.makedirs(folder_path)
        except FileExistsError:
            pass
        except OSError as error:
            print(f"Error creating folder '{folder_path}': {error}")

    def create_config_folder_and_default(self, source_name, collection_name):
        """
        sinequa configs are source_name/collection_name/default.xml
        makes a folder named after the collection with a default.xml inside of it
        does this inside of the the specified source folder
        """

        # Create a folder named after source inside the desired directory
        config_folder_path = os.path.join(source_name, collection_name)
        self.create_folder_if_needed(config_folder_path)
        xml_path = os.path.join(config_folder_path, "default.xml")

        # self._write_xml(xml_path)
        self._update_config_xml(xml_path)

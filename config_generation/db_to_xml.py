import json
import xml.etree.ElementTree as ET

import xmltodict

from sde_collections.models.collection_choice_fields import (
    ConnectorChoices,
    DocumentTypes,
)


class XmlEditor:
    """
    Class is instantiated with a path to an xml.
    An internal etree is generated, and changes are made in place.
    An ouput path is given and the etree is saved to it.
    """

    def __init__(self, xml_string: str):
        self.xml_tree = self._get_tree(xml_string)

    def _get_tree(self, xml_string) -> ET.ElementTree:
        """takes the path of an xml file and opens it as an ElementTree object"""
        return ET.ElementTree(ET.fromstring(xml_string))

    def get_tag_value(self, tag_name: str) -> list:
        """
        tag_name can be either the top level tag
        or you can get a child by saying 'parent/child'
        """
        return [element.text for element in self.xml_tree.findall(tag_name)]

    def _add_declaration(self, xml_string: str):
        """adds xml declaration to xml string"""
        declaration = """<?xml version="1.0" encoding="utf-8"?>\n"""

        return declaration + xml_string

    def update_config_xml(self):
        xml_string = ET.tostring(
            self.xml_tree.getroot(),
            encoding="utf8",
            method="html",
            xml_declaration=True,
        )
        xml_string = xml_string.decode("utf-8")

        xml_string = self._add_declaration(xml_string)
        xml_string = self._resave_pretty(xml_string)

        return xml_string

    def _resave_pretty(self, xml_string):
        """opens and resaves a file to reformat it"""

        xml = xmltodict.parse(xml_string)
        return xmltodict.unparse(xml, pretty=True)

    def update_or_add_element_value(self, path, new_value, parent_element_name=None):
        """
        Update or create a value in the XML.

        Parameters:
        - xml_string (str): The original XML string.
        - path (str): The path to the element. Elements are separated by '/'. Example: 'root/child/grandchild'
        - new_value (str): The new value to set.

        Returns:
        - str: The updated XML string.
        """

        # Parse the XML string into an ElementTree
        root = self.xml_tree.getroot()

        # Split the path into its components
        if parent_element_name is not None:
            path = f"{parent_element_name}/{path}"
        elements = path.split("/")

        # Traverse and/or create the path
        current_element = root
        for element in elements:  # Skip the root element
            # If the child exists, move to it; otherwise, create it
            next_element = current_element.find(element)
            if next_element is None:
                next_element = ET.SubElement(current_element, element)
            current_element = next_element

        # Set the value
        current_element.text = new_value

        # Return the updated XML as a string
        return ET.tostring(root, encoding="utf-8").decode("utf-8")

    def convert_indexer_to_scraper(self) -> None:
        """
        assuming this class has been instantiated with a previously constructed indexer config
        some values must now be modified so it will be an effective scraper
        """
        self.update_or_add_element_value("Indexers", "")
        self.update_or_add_element_value(
            "Plugin", "SMD_Plugins/Sinequa.Plugin.ListCandidateUrls"
        )
        self.update_or_add_element_value("ShardIndexes", "")
        self.update_or_add_element_value("ShardingStrategy", "")
        self.update_or_add_element_value("WorkerCount", "8")
        self.update_or_add_element_value("LogLevel", "0", parent_element_name="System")
        self.update_or_add_element_value(
            "Simulate", "true", parent_element_name="IndexerClient"
        )

    def convert_scraper_to_indexer(self) -> None:
        # this is specialized for the production instance right now
        self.update_or_add_element_value("Indexers", "")
        self.update_or_add_element_value("Plugin", "")
        self.update_or_add_element_value(
            "Identity", "NodeIndexer1/identity0"
        )  # maybe make this blank?
        self.update_or_add_element_value("ShardIndexes", "")
        self.update_or_add_element_value("ShardingStrategy", "")
        self.update_or_add_element_value("WorkerCount", "8")
        self.update_or_add_element_value("LogLevel", "20", parent_element_name="System")
        self.update_or_add_element_value(
            "Simulate", "false", parent_element_name="IndexerClient"
        )

    def convert_template_to_scraper(self, url: str) -> None:
        """
        assuming this class has been instantiated with the scraper_template.xml
        the only remaining step is to add the base url to be scraped
        """
        self.update_or_add_element_value("Url", url)

    def _mapping_exists(self, new_mapping: ET.Element):
        """
        Check if the mapping with given parameters already exists in the XML tree
        """
        xml_root = self.xml_tree.getroot()

        for mapping in xml_root.findall("Mapping"):
            existing_mapping = {
                child.tag: (child.text if child.text is not None else "")
                for child in mapping
            }
            new_mapping_dict = {
                child.tag: (child.text if child.text is not None else "")
                for child in new_mapping
            }
            if existing_mapping == new_mapping_dict:
                return True

        return False

    @staticmethod
    def _standardize_selection(selection):
        """
        some existing selections may use double quotes while new ones need to use single quotes
        # prior rule generations were not as selective, so some old selections used a trailing *
        #     while the new selection will not
        this function creates two selections that will match against the old format and allow it to
            be replaced by the _generic_mapping function
        """
        standardized_quotes = selection.replace('"', "'")
        # standardized_quotes_less_selective = standardized_quotes.replace(
        #     "*'</Selection>", "'</Selection>"
        # )

        return list(
            set(selection, standardized_quotes)  # , standardized_quotes_less_selective)
        )

    def _generic_mapping(
        self,
        name: str = "",
        description: str = "",
        value: str = "",
        selection: str = "",
    ):
        """
        most mappings take the same fields, so this gives a generic way to make a mapping
        """
        xml_root = self.xml_tree.getroot()

        existing_mapping = None
        for mapping in xml_root.findall("Mapping"):
            mapping_name = mapping.find("Name")
            mapping_selection = mapping.find("Selection")

            if (
                mapping_name
                and mapping_name.text == name
                and mapping_selection
                and mapping_selection.text in self._standardize_selection(selection)
            ):
                existing_mapping = mapping
                break

        if existing_mapping:
            # If an existing mapping is found, overwrite its values
            existing_mapping_value = existing_mapping.find("Value")
            if existing_mapping_value:
                existing_mapping_value.text = value
        else:
            # If no existing mapping is found, create a new one
            mapping = ET.Element("Mapping")
            ET.SubElement(mapping, "Name").text = name
            ET.SubElement(mapping, "Description").text = description
            ET.SubElement(mapping, "Value").text = value
            ET.SubElement(mapping, "Selection").text = selection
            ET.SubElement(mapping, "DefaultValue").text = ""
            xml_root.append(mapping)

    def add_document_type_mapping(self, document_type: str, criteria: str) -> None:
        if criteria:
            selection = f"doc.url1 match '{criteria}'"
        else:
            selection = ""
        self._generic_mapping(
            name="sourcestr56",
            value=f'"{document_type}"',
            selection=selection,
        )

    def add_title_mapping(self, title_value: str, title_criteria: str) -> None:
        title_criteria = title_criteria.rstrip("/")
        sinequa_code_markers = ["xpath", "Concat", "IfEmpty", "doc.title", "doc.url1"]
        if not any(marker in title_value for marker in sinequa_code_markers):
            # exact title replacements need quotes
            # sinequa code needs to NOT have quotes
            title_value = f'"{title_value}"'

        self._generic_mapping(
            name="title",
            value=title_value,
            selection=f"doc.url1 match '{title_criteria}'",
        )

    def add_job_list_item(self, job_name):
        """
        this is specifically for editing joblist templates by adding a new collection to a joblist
        config_generation/xmls/joblist_template.xml
        """
        xml_root = self.xml_tree.getroot()

        mapping = ET.Element("JobListItem")
        ET.SubElement(mapping, "Name").text = job_name
        ET.SubElement(mapping, "StopOnError").text = "false"
        xml_root.append(mapping)

    def add_id(self) -> None:
        self._generic_mapping(
            name="id",
            value="doc.url1",
        )

    def add_document_type(self, document_type: str) -> None:
        self._generic_mapping(
            name="sourcestr56",
            value=f'"{document_type}"',
        )

    def add_xpath_indexing_filter(self, xpath: str, selection: str = "") -> None:
        # TODO: take in selection as an arg
        """filters out the content of an xpath from being indexed along with the document"""

        xml_root = self.xml_tree.getroot()

        mapping = ET.Element("IndexingFilter")
        ET.SubElement(mapping, "XPath").text = xpath
        ET.SubElement(mapping, "IncludeMode").text = "false"
        ET.SubElement(mapping, "Selection").text = selection
        xml_root.append(mapping)

    def add_url_exclude(self, url_pattern: str) -> None:
        """
        excludes a url or url pattern, such as
        - https://webb.nasa.gov/content/forEducators/realworld*
        - https://webb.nasa.gov/content/features/index.html
        - *.rtf
        """

        xml_root = self.xml_tree.getroot()

        for url_index_excluded in xml_root.findall("UrlIndexExcluded"):
            if url_index_excluded.text == url_pattern:
                return  # stop the function if the url pattern already exists

        # add the url pattern if it doesn't already exist
        ET.SubElement(xml_root, "UrlIndexExcluded").text = url_pattern

    def add_url_include(self, url_pattern: str) -> None:
        """
        includes a url or url pattern, such as
        - https://webb.nasa.gov/content/forEducators/realworld*
        - https://webb.nasa.gov/content/features/index.html
        - *.rtf
        I'm not sure if exclusion rules override includes or if includes override
        exclusion rules.
        """

        xml_root = self.xml_tree.getroot()

        for url_index_included in xml_root.findall("UrlIndexIncluded"):
            if url_index_included.text == url_pattern:
                return  # stop the function if the url pattern already exists

        # add the url pattern if it doesn't already exist
        ET.SubElement(xml_root, "UrlIndexIncluded").text = url_pattern

    def _find_treeroot_field(self):
        treeroot = self.xml_tree.find("TreeRoot")
        if treeroot is None:
            treeroot = self.xml_tree.find("treeRoot")
        return treeroot

    def fetch_treeroot(self):
        treeroot = self._find_treeroot_field()
        return treeroot.text

    def fetch_division_name(self):
        # this is pretty brittle and can break easily if the treeRoot field is changed
        treeroot = self.fetch_treeroot()
        splits = [split for split in treeroot.split("/") if split]
        try:
            division, name = splits
        except ValueError:
            print(f"Could not find division and name in {treeroot}")
            division = ""
            name = ""
        return division, name

    def fetch_url(self):
        url = self.xml_tree.find("Url")
        if url is None:
            url = self.xml_tree.find("url")
        try:
            return url.text
        except AttributeError:
            return ""

    def fetch_document_type(self):
        DOCUMENT_TYPE_COLUMN = "sourcestr56"
        try:
            document_type_text = self.xml_tree.find(
                f"Mapping[Name='{DOCUMENT_TYPE_COLUMN}']/Value"
            ).text
        except AttributeError:
            return None

        try:
            document_type = DocumentTypes.lookup_by_text(json.loads(document_type_text))
        except json.decoder.JSONDecodeError:
            document_type = None
        return document_type

    def fetch_connector(self):
        connector = self.xml_tree.find("Connector")
        if connector is None:
            connector = self.xml_tree.find("connector")

        if connector is None:
            connector = ConnectorChoices.NO_CONNECTOR
        elif connector.text.strip() == "crawler2":
            connector = ConnectorChoices.CRAWLER2
        elif connector.text.strip() == "json":
            connector = ConnectorChoices.JSON
        elif connector.text.strip() == "hyperindex":
            connector = ConnectorChoices.HYPERINDEX
        else:  # as a catch all
            connector = ConnectorChoices.NO_CONNECTOR
        return connector

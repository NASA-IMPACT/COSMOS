import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


class XmlEditor:
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

    def get_tag_value(self, tag_name: str) -> list:
        """
        tag_name can be either the top level tag
        or you can get a child by saying 'parent/child'
        """
        return [element.text for element in self.xml_tree.findall(tag_name)]

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

    # def _write_xml(self, output_path: str) -> None:
    #     """
    #     takes the self.xml_tree ElementTree object and writes it to an output path

    #     although this function can be used on it's own to write a one-off file, most
    #     config files are actually called default.xml and nested inside a folder,
    #     therefore create_config_folder_and_default is the usual way to make files
    #     """

    #     xml_root = self.xml_tree.getroot()
    #     pretty_xml = self.prettify(xml_root)

    #     with open(output_path, "w", encoding="utf-8") as output_file:
    #         output_file.write(pretty_xml)

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

    # def expand_empty_tags(self, xml_string: str) -> str:
    #     """
    #     etree replaces <></> tags with </> essentially converting empty tag pairs
    #     to self closing tags. this is not sinequa standard. so this function undoes this behavior
    #     """
    #     return re.sub(r"<([^/][^<>]*[^/])/>", r"<\1></\1>", xml_string)

    # def prettify(self, element: ET.Element) -> str:
    #     """
    #     By default, the output xml will have extra new lines, self-closing tags
    #     and weird indents. This function makes all that sinequa standard.
    #     """

    #     rough_string = ET.tostring(element, "unicode")
    #     reparsed = minidom.parseString(rough_string)
    #     pretty_xml = reparsed.toprettyxml(indent="    ")
    #     pretty_xml = self.expand_empty_tags(pretty_xml)

    #     return "\n".join([line for line in pretty_xml.split("\n") if line.strip()])

    def update_or_add_element_value(
        self,
        element_name: str,
        element_value: str,
        parent_element_name: str = None,
    ) -> None:
        """can update the value of either a top level or secondary level value in the sinequa config

        Args:
            element_name (str): name of the sinequa element, such as "Simulate"
            element_value (str): value to be stored to element, such as "false"
            parent_element_name (str, optional): parent of the element, such as "IndexerClient"
               Defaults to None.
        """

        xml_root = self.xml_tree.getroot()
        parent_element = (
            xml_root
            if parent_element_name is None
            else xml_root.find(parent_element_name)
        )

        existing_element = parent_element.find(element_name)
        if existing_element is not None:
            existing_element.text = element_value
        else:
            ET.SubElement(parent_element, element_name).text = element_value

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

        mapping = ET.Element("Mapping")
        ET.SubElement(mapping, "Name").text = name
        ET.SubElement(mapping, "Description").text = description
        ET.SubElement(mapping, "Value").text = value
        ET.SubElement(mapping, "Selection").text = selection
        ET.SubElement(mapping, "DefaultValue").text = ""
        xml_root.append(mapping)

    def add_title_mapping(
        self, title_value: str, title_criteria: str
    ) -> ET.ElementTree:
        title_criteria = title_criteria.rstrip("/")
        if "xpath" not in title_value:
            # exact title replacements need quotes
            # xpath title rules need to NOT have quotes
            title_value = f'"{title_value}"'

        self._generic_mapping(
            name="title",
            value=title_value,
            selection=f'doc.url1 match "{title_criteria}"',
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
        ET.SubElement(
            xml_root, "UrlIndexExcluded"
        ).text = url_pattern  # this adds an indexing rule (doesn't overwrite)

    def add_url_include(self, url_pattern: str) -> None:
        """
        includes a url or url pattern, such as
        - https://webb.nasa.gov/content/forEducators/realworld*
        - https://webb.nasa.gov/content/features/index.html
        I'm not sure if exclusion rules override includes or if includes override
        exclusion rules.
        """

        xml_root = self.xml_tree.getroot()
        ET.SubElement(
            xml_root, "UrlIndexIncluded"
        ).text = url_pattern  # this adds an indexing rule (doesn't overwrite)

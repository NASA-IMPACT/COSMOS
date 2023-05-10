import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


class XmlEditor:
    """
    Class is instantiated with a path to an xml.
    An internal etree is generated, and changes are made in place.
    An ouput path is given and the etree is saved to it.
    """

    def __init__(self, xml_path):
        self.input_path = xml_path
        self.xml_tree = self.get_tree(self.input_path)

    def get_tree(self, xml_path) -> ET.ElementTree:
        """takes the path of an xml file and opens it as an ElementTree object"""
        return ET.parse(xml_path)

    def write_xml(self, output_path: str) -> None:
        """takes the self.xml_tree ElementTree object and writes it to an output path"""
        xml_root = self.xml_tree.getroot()
        pretty_xml = self.prettify(xml_root)

        with open(output_path, "w", encoding="utf-8") as output_file:
            output_file.write(pretty_xml)

    def expand_empty_tags(self, xml_string: str) -> str:
        """
        etree replaces <></> tags with </> essentially converting empty tag pairs
        to self closing tags. this is not sinequa standard. so this function undoes this behavior
        """
        return re.sub(r"<([^/][^<>]*[^/])/>", r"<\1></\1>", xml_string)

    def prettify(self, element: ET.Element) -> str:
        """
        By default, the output xml will have extra new lines, self-closing tags
        and weird indents. This function makes all that sinequa standard.
        """

        rough_string = ET.tostring(element, "unicode")
        reparsed = minidom.parseString(rough_string)
        pretty_xml = reparsed.toprettyxml(indent="    ")
        pretty_xml = self.expand_empty_tags(pretty_xml)

        return "\n".join([line for line in pretty_xml.split("\n") if line.strip()])

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

    def convert_template_to_scraper(self, url: str) -> None:
        """
        assuming this class has been instantiated with the scraper_template.xml
        the only remaining step is to add the base url to be scraped
        """
        self.update_or_add_element_value("Url", url)

    # def add_title_mapping(
    #     self, title_value: str, title_criteria: str
    # ) -> ET.ElementTree:
    #     xml_root = self.xml_tree.getroot()

    #     mapping = ET.Element("Mapping")
    #     ET.SubElement(mapping, "Name").text = "title"
    #     ET.SubElement(mapping, "Description").text = "Custom title for certain criteria"
    #     ET.SubElement(mapping, "Value").text = title_value
    #     ET.SubElement(mapping, "Selection").text = title_criteria
    #     xml_root.append(mapping)

    #     # TODO: is this function correct?
    #     self.xml_tree = xml_tree

    # def add_indexing_filter(self, xpath: str) -> ET.ElementTree:
    #     # TODO: is this function correct?
    #     xml_root = self.xml_tree.getroot()

    #     mapping = ET.Element("IndexingFilter")
    #     ET.SubElement(mapping, "XPath").text = xpath

    #     xml_root.append(mapping)

    #     self.xml_tree = xml_root
    #     return xml_tree

    # def add_tree_root(xml_tree: ET.ElementTree, tree_root: str) -> ET.ElementTree:
    #     xml_root = xml_tree.getroot()
    #     ET.SubElement(xml_root, "TreeRoot").text = tree_root
    #     return xml_tree

    # def add_url_exclude(xml_tree: ET.ElementTree, url: str) -> ET.ElementTree:
    #     # TODO: replace this with the linking exclude
    #     xml_root = xml_tree.getroot()
    #     ET.SubElement(xml_root, "UrlIndexExcluded").text = url
    #     return xml_tree


# def example_full_create() -> None:
#     tree_root = "/Webb/"
#     primary_url = "https://webb.nasa.gov/"
#     title_data = [
#         {"title_value": "My Custom Title", "title_criteria": "my pattern"},
#     ]
#     indexing_filters = [
#         {
#             "xpath": '//*[@id="jwstFooter"]',
#         },
#         {"xpath": '//*[@id="ssdBgWrapper"]/header'},
#     ]

#     url_excludes = [
#         "https://webb.nasa.gov/content/forEducators/realworld*",
#         "*.rtf",
#         "https://webb.nasa.gov/content/features/index.html",
#         "https://webb.nasa.gov/content/features/jwstArt/index.html",
#         "https://webb.nasa.gov/content/webbLaunch/whereIsWebb*",
#         "https://webb.nasa.gov/content/webbLaunch/news.html",
#         "https://webb.nasa.gov/index.html",
#         "https://webb.nasa.gov/index.html",
#         "https://webb.nasa.gov/content/news/webbBuildStatusArchive.html",
#         "https://webb.nasa.gov/content/news/index.html",
#         "https://webb.nasa.gov/content/news/",
#     ]

#     xml_tree = get_tree()

#     xml_tree = add_primary_url(xml_tree, primary_url)
#     xml_tree = add_tree_root(xml_tree, tree_root)
#     for url in url_excludes:
#         xml_tree = add_url_exclude(xml_tree, url)
#     for title_dict in title_data:
#         xml_tree = add_title_mapping(xml_tree=xml_tree, **title_dict)
#     for indexing_dict in indexing_filters:
#         xml_tree = add_indexing_filter(xml_tree=xml_tree, **indexing_dict)

#     write_xml(xml_tree, "output.xml")

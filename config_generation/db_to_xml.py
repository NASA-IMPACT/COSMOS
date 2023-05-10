import re
import xml.etree.ElementTree as ET
from xml.dom import minidom


def expand_empty_tags(xml_string: str) -> str:
    """
    etree replaces <></> tags with </> essentially converting empty tag pairs
    to self closing tags. this is not sinequa standard. so this function undoes this behavior
    """
    return re.sub(r"<([^/][^<>]*[^/])/>", r"<\1></\1>", xml_string)


def prettify(element: ET.Element) -> str:
    """
    By default, the output xml will have extra new lines, self-closing tags
    and weird indents. This function makes all that sinequa standard.
    """
    rough_string = ET.tostring(element, "unicode")
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")
    pretty_xml = expand_empty_tags(pretty_xml)
    return "\n".join([line for line in pretty_xml.split("\n") if line.strip()])


def get_tree(xml_path: str = "blank_sinequa_template.xml") -> ET.ElementTree:
    return ET.parse(xml_path)


def write_xml(xml_tree: ET.ElementTree, xml_path: str) -> None:
    xml_root = xml_tree.getroot()
    pretty_xml = prettify(xml_root)

    with open(xml_path, "w", encoding="utf-8") as output_file:
        output_file.write(pretty_xml)


def add_title_mapping(
    xml_tree: ET.ElementTree, title_value: str, title_criteria: str
) -> ET.ElementTree:
    xml_root = xml_tree.getroot()

    mapping = ET.Element("Mapping")
    ET.SubElement(mapping, "Name").text = "title"
    ET.SubElement(mapping, "Description").text = "Custom title for certain criteria"
    ET.SubElement(mapping, "Value").text = title_value
    ET.SubElement(mapping, "Selection").text = title_criteria

    xml_root.append(mapping)

    return xml_tree


def add_indexing_filter(xml_tree: ET.ElementTree, xpath: str) -> ET.ElementTree:
    xml_root = xml_tree.getroot()

    mapping = ET.Element("IndexingFilter")
    ET.SubElement(mapping, "XPath").text = xpath

    xml_root.append(mapping)

    return xml_tree


def add_primary_url(xml_tree: ET.ElementTree, primary_url: str) -> ET.ElementTree:
    xml_root = xml_tree.getroot()
    ET.SubElement(xml_root, "Url").text = primary_url
    return xml_tree


def add_tree_root(xml_tree: ET.ElementTree, tree_root: str) -> ET.ElementTree:
    xml_root = xml_tree.getroot()
    ET.SubElement(xml_root, "TreeRoot").text = tree_root
    return xml_tree


def add_url_exclude(xml_tree: ET.ElementTree, url: str) -> ET.ElementTree:
    # TODO: replace this with the linking exclude
    xml_root = xml_tree.getroot()
    ET.SubElement(xml_root, "UrlIndexExcluded").text = url
    return xml_tree


def update_or_add_element_value(
    xml_tree: ET.ElementTree,
    element_name: str,
    element_value: str,
    parent_element_name: str = None,
) -> ET.ElementTree:
    xml_root = xml_tree.getroot()

    parent_element = (
        xml_root if parent_element_name is None else xml_root.find(parent_element_name)
    )

    existing_element = parent_element.find(element_name)
    if existing_element is not None:
        existing_element.text = element_value
    else:
        ET.SubElement(parent_element, element_name).text = element_value

    return xml_tree


def convert_indexer_to_scraper(xml_input_path: str, xml_output_path: str) -> None:
    xml_tree = get_tree(xml_input_path)
    xml_tree = update_or_add_element_value(xml_tree, "Indexers", "")
    xml_tree = update_or_add_element_value(
        xml_tree, "Plugin", "SMD_Plugins/Sinequa.Plugin.ListCandidateUrls"
    )
    xml_tree = update_or_add_element_value(xml_tree, "ShardIndexes", "")
    xml_tree = update_or_add_element_value(xml_tree, "ShardingStrategy", "")
    xml_tree = update_or_add_element_value(xml_tree, "WorkerCount", "8")

    xml_tree = update_or_add_element_value(
        xml_tree, "LogLevel", "0", parent_element_name="System"
    )
    xml_tree = update_or_add_element_value(
        xml_tree, "Simulate", "false", parent_element_name="IndexerClient"
    )

    write_xml(xml_tree, xml_output_path)


def example_full_create() -> None:
    tree_root = "/Webb/"
    primary_url = "https://webb.nasa.gov/"
    title_data = [
        {"title_value": "My Custom Title", "title_criteria": "my pattern"},
    ]
    indexing_filters = [
        {
            "xpath": '//*[@id="jwstFooter"]',
        },
        {"xpath": '//*[@id="ssdBgWrapper"]/header'},
    ]

    url_excludes = [
        "https://webb.nasa.gov/content/forEducators/realworld*",
        "*.rtf",
        "https://webb.nasa.gov/content/features/index.html",
        "https://webb.nasa.gov/content/features/jwstArt/index.html",
        "https://webb.nasa.gov/content/webbLaunch/whereIsWebb*",
        "https://webb.nasa.gov/content/webbLaunch/news.html",
        "https://webb.nasa.gov/index.html",
        "https://webb.nasa.gov/index.html",
        "https://webb.nasa.gov/content/news/webbBuildStatusArchive.html",
        "https://webb.nasa.gov/content/news/index.html",
        "https://webb.nasa.gov/content/news/",
    ]

    xml_tree = get_tree()

    xml_tree = add_primary_url(xml_tree, primary_url)
    xml_tree = add_tree_root(xml_tree, tree_root)
    for url in url_excludes:
        xml_tree = add_url_exclude(xml_tree, url)
    for title_dict in title_data:
        xml_tree = add_title_mapping(xml_tree=xml_tree, **title_dict)
    for indexing_dict in indexing_filters:
        xml_tree = add_indexing_filter(xml_tree=xml_tree, **indexing_dict)

    write_xml(xml_tree, "output.xml")


if __name__ == "__main__":
    convert_indexer_to_scraper("helio.xml", "helio.xml")

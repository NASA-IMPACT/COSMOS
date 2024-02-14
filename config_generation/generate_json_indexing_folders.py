import os
import shutil
import xml.etree.ElementTree as ET

import xmltodict

sources = [
    {
        "name": "solar_system_exploration",
        "treepath": "/Planetary Science/Solar System Exploration/",
        "page_number": "1221",
    },
    {
        "name": "Geosciences_Node",
        "treepath": "/Planetary Science/PDS Geosciences Node/",
        "page_number": "10",
    },
    {
        "name": "Small_Bodies_Node",
        "treepath": "/Planetary Science/Small Bodies Node/",
        "page_number": "2",
    },
    {
        "name": "pds_rings",
        "treepath": "/Planetary Science/PDS Ring Moon Systems Node/",
        "page_number": "445",
    },
    {
        "name": "ppi_node",
        "treepath": "/Planetary Science/Planetary Plasma Interactions (PPI) Node/",
        "page_number": "8",
    },
    {
        "name": "pds_cartography_and_imaging_sciences_node",
        "treepath": "/Planetary Science/PDS Cartography and Imaging Sciences Node/",
        "page_number": "3",
    },
    {
        "name": "pds_atmospheres",
        "treepath": "/Planetary Science/PDS Planetary Atmospheres Node/",
        "page_number": "3",
    },
]


def resave_pretty(output_path):
    """opens and resaves a file to reformat it"""

    with open(output_path) as f:
        xml_data = f.read()
    xml = xmltodict.parse(xml_data)
    with open(output_path, "w") as f:
        f.write(xmltodict.unparse(xml, pretty=True))


def update_tree_root(xml_path, new_value):
    """
    Update the text value of <TreeRoot> element under the root element, expected to be <Sinequa>.

    :param xml_path: Path to the XML file to be updated.
    :param new_value: New value to set for the <TreeRoot> element.
    """
    # Parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Find the <TreeRoot> element directly under the root (which should be <Sinequa>)
    tree_root = root.find("TreeRoot")
    if tree_root is not None:
        # Update the text value of <TreeRoot>
        tree_root.text = new_value
        # Save the changes back to the file
        tree.write(xml_path, encoding="utf-8", xml_declaration=True, method="xml")

    else:
        print("TreeRoot element not found.")


def update_xml_values(xml_path, updates):
    """
    Update specified values within the <DataSource> section of an XML file.

    :param xml_path: Path to the XML file to be updated.
    :param updates: Dictionary where keys are paths relative to <DataSource> and values are the new values to be set.
    """
    # Parse the XML file
    tree = ET.parse(xml_path)
    root = tree.getroot()

    # Navigate to the <DataSource> section
    data_source = root.find(".//DataSource")
    if data_source is not None:
        for path, new_value in updates.items():
            # Find the specific element within DataSource to update
            element_to_update = data_source.find(path)
            if element_to_update is not None:
                # Update the text value of the element
                element_to_update.text = new_value
            else:
                print(f"Element '{path}' not found within DataSource.")
    else:
        print("DataSource section not found in the XML.")

    # Save the changes back to the file
    tree.write(xml_path, encoding="utf-8", xml_declaration=True, method="xml")


# Specify the path to your XML file
xml_file_path = "json_url_indexing_template.xml"

# Iterate over each source in the list
for source in sources:
    # Get the folder name from the source
    folder_name = source["name"]

    # Check if the folder already exists; if not, create it
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)

    # Define the destination path for the XML file
    destination_path = os.path.join(folder_name, os.path.basename("default.xml"))

    # Copy the XML file to the new location
    shutil.copy(xml_file_path, destination_path)

    updates = {
        "Source": f'https://sde-indexing-helper.nasa-impact.net/candidate-urls-api/{source["name"]}/',
        "NextPageExpression": "https://sde-indexing-helper.nasa-impact.net/candidate-urls-api/"
        + source["name"]
        + "/?format=json&amp;page={Add(datasource.url_list.pagenumber,1)}",
        "EndPageExpression": f'datasource.url_list.pagenumber={source["page_number"]}',
    }
    update_xml_values(destination_path, updates)
    update_tree_root(destination_path, source["treepath"])

    resave_pretty(destination_path)

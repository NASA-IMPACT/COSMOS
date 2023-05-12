import os

import xmltodict


def open_xml_as_dict(path):
    with open(path) as fd:
        xml_dict = xmltodict.parse(fd.read())
    return xml_dict


def save_xml(save_path, xml_dict):
    xml_string = xmltodict.unparse(xml_dict, pretty=True)
    with open(save_path, "w") as xmlfile:
        xmlfile.write(xml_string)


def create_folder(folder_name):
    try:
        os.makedirs(folder_name)
    except FileExistsError:
        pass
    except OSError as error:
        print(f"Error creating folder '{folder_name}': {error}")


def create_config_folder_and_default(path_for_config_folder, source_name, xml_dict):
    """
    makes a folder named after the source with a default.xml inside of it
    does this inside of the config_generation_scripts
    """

    # Create a folder named after source inside the desired directory
    config_folder = os.path.join(path_for_config_folder, source_name)
    create_folder(config_folder)
    xml_path = os.path.join(config_folder, "default.xml")

    save_xml(xml_path, xml_dict)

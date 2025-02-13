from xml.etree.ElementTree import ElementTree, ParseError, fromstring

from ..db_to_xml import XmlEditor


def xmls_equal(xml1, xml2):
    """
    Check the structural and textual equality of two XML strings.

    Parameters:
    - xml1, xml2 (str): The XML strings to compare.

    Returns:
    - bool: True if XMLs are structurally and textually equal, False otherwise.
    """

    def elements_equal(e1, e2):
        # Check tag and text
        if e1.tag != e2.tag or (e1.text or "").strip() != (e2.text or "").strip():
            return False

        # Check attributes (ignoring order)
        if sorted(e1.attrib.items()) != sorted(e2.attrib.items()):
            return False

        # Check children
        if len(e1) != len(e2):
            return False
        return all(elements_equal(c1, c2) for c1, c2 in zip(e1, e2))

    tree1 = ElementTree(fromstring(xml1))
    tree2 = ElementTree(fromstring(xml2))

    return elements_equal(tree1.getroot(), tree2.getroot())


# Tests for valid and invalid XML initializations
def test_valid_xml_initialization():
    xml_string = "<root><child>Test</child></root>"
    editor = XmlEditor(xml_string)
    assert editor.get_tag_value("child") == ["Test"]


def test_invalid_xml_initialization():
    with pytest.raises(ParseError):
        XmlEditor("<root><child></root>")


# Test retrieval of single and multiple tag values
def test_get_single_tag_value():
    xml_string = "<root><child>Test</child></root>"
    editor = XmlEditor(xml_string)
    assert editor.get_tag_value("child", strict=True) == "Test"


def test_get_nonexistent_tag_value():
    xml_string = "<root><child>Test</child></root>"
    editor = XmlEditor(xml_string)
    assert editor.get_tag_value("nonexistent", strict=False) == []


def test_get_tag_value_strict_multiple_elements():
    xml_string = "<root><child>One</child><child>Two</child></root>"
    editor = XmlEditor(xml_string)
    with pytest.raises(ValueError):
        editor.get_tag_value("child", strict=True)


# Test updating and adding XML elements
def test_update_existing_element():
    xml_string = "<root><child>Old</child></root>"
    editor = XmlEditor(xml_string)
    editor.update_or_add_element_value("child", "New")
    updated_xml = editor.update_config_xml()
    assert "New" in updated_xml and "Old" not in updated_xml


def test_add_new_element():
    xml_string = "<root></root>"
    editor = XmlEditor(xml_string)
    editor.update_or_add_element_value("newchild", "Value")
    updated_xml = editor.update_config_xml()
    assert "Value" in updated_xml and "<newchild>Value</newchild>" in updated_xml


def test_add_complex_element_structure():
    xml_string = "<root></root>"
    editor = XmlEditor(xml_string)
    editor.update_or_add_element_value("parent/child", "Nested")
    updated_xml = editor.update_config_xml()
    assert "Nested" in updated_xml and "<child>Nested</child>" in updated_xml


# Test transformations and generic mapping
def test_convert_indexer_to_scraper_transformation():
    xml_string = """<root><Plugin>Indexer</Plugin></root>"""
    editor = XmlEditor(xml_string)
    editor.convert_indexer_to_scraper()
    updated_xml = editor.update_config_xml()
    assert "<Plugin>SMD_Plugins/Sinequa.Plugin.ListCandidateUrls</Plugin>" in updated_xml
    assert "<Plugin>Indexer</Plugin>" not in updated_xml


def test_generic_mapping_addition():
    xml_string = "<root></root>"
    editor = XmlEditor(xml_string)
    editor._generic_mapping(name="id", value="doc.url1", selection="url1")
    updated_xml = editor.update_config_xml()
    assert "<Mapping>" in updated_xml
    assert "<Name>id</Name>" in updated_xml
    assert "<Value>doc.url1</Value>" in updated_xml


# Test XML serialization with headers
def test_xml_serialization_with_header():
    xml_string = "<root><child>Value</child></root>"
    editor = XmlEditor(xml_string)
    xml_output = editor.update_config_xml()
    assert '<?xml version="1.0" encoding="utf-8"?>' in xml_output
    assert "<root>" in xml_output and "<child>Value</child>" in xml_output


# Test handling multiple changes accumulation
def test_multiple_changes_accumulation():
    xml_string = "<root><child>Initial</child></root>"
    editor = XmlEditor(xml_string)
    editor.update_or_add_element_value("child", "Modified")
    editor.update_or_add_element_value("newchild", "Added")
    updated_xml = editor.update_config_xml()
    assert "Modified" in updated_xml and "Added" in updated_xml
    assert "Initial" not in updated_xml

import xml.etree.ElementTree as ET

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

    tree1 = ET.fromstring(xml1)
    tree2 = ET.fromstring(xml2)
    return elements_equal(tree1, tree2)


def test_update_or_add_element_value():
    xml_string = """<root>
    <child>
        <grandchild>old_value</grandchild>
    </child>
    </root>"""

    editor = XmlEditor(xml_string)

    # To update an existing element's value
    updated_xml = editor.update_or_add_element_value(
        "root/child/grandchild", "new_value"
    )
    expected_output = """<root>
        <child>
            <grandchild>new_value</grandchild>
        </child>
    </root>
    """
    assert xmls_equal(updated_xml, expected_output)

    # To create a new element and set its value
    new_xml = editor.update_or_add_element_value("root/newchild", "some_value")
    expected_output = """<root>
        <child>
            <grandchild>new_value</grandchild>
        </child>
        <newchild>
            some_value
        </newchild>
    </root>
    """
    assert xmls_equal(new_xml, expected_output)

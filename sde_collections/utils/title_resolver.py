import _ast
import ast
import html as html_lib
import re
from typing import Any

import requests
from lxml import etree, html
from unidecode import unidecode


def is_valid_xpath(xpath: str) -> bool:
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def is_valid_fstring(pattern: str) -> bool:
    context = {
        "url": "",
        "title": "",
        "collection": "",
    }
    parsed = ast.parse(f"f'''{pattern}'''", mode="eval")
    # Walk through the AST to ensure it only contains safe expressions
    for node in ast.walk(parsed):
        if isinstance(node, _ast.FormattedValue):
            if not isinstance(node.value, _ast.Name):
                raise ValueError("Unsupported expression in f-string pattern.")
            if node.value.id not in context:
                variables_allowed = ", ".join([key for key in context.keys()])
                raise ValueError(
                    f"Variable '{node.value.id}' not allowed in f-string pattern."
                    f" Allowed variables are: {variables_allowed}"
                )


def clean_text(text: str) -> str:
    text_content = unidecode(text)
    text_content = html_lib.unescape(text_content)
    # remove tabs and newlines, replace them with a single space
    text_content = re.sub(r"[\t\n\r]+", " ", text_content)
    # remove multiple spaces
    text_content = re.sub(r"\s+", " ", text_content)
    # strip leading and trailing whitespace
    text_content = text_content.strip()
    return text_content


def resolve_brace(pattern: str, context: dict[str, Any]) -> str:
    """Safely interpolates the variables in an f-string pattern using the provided context."""
    parsed = ast.parse(f"f'''{pattern}'''", mode="eval")

    is_valid_fstring(pattern)  # Refactor this

    compiled = compile(parsed, "<string>", "eval")
    return str(eval(compiled, {}, context))


def resolve_xpath(xpath: str, url: str) -> str:
    if not is_valid_xpath(xpath):
        raise ValueError(f"The xpath, {xpath}, is not valid.")

    response = requests.get(url)

    if response.ok:
        tree = html.fromstring(response.content)
        values = tree.xpath(xpath)

        if len(values) == 1:
            text_content = values[0].text
            if text_content:
                text_content = clean_text(text_content)
                return text_content
            else:
                raise ValueError(f"The element at the xpath, {xpath}, does not contain any text content.")
        elif len(values) > 1:
            raise ValueError(f"More than one element found for the xpath, {xpath}")
        else:
            raise ValueError(f"No element found for the xpath, {xpath}")
    else:
        raise ValueError(f"Failed to retrieve the {url}. Status code: {response.status_code}")


def parse_title(input_string: str) -> list[tuple[str, str]]:
    brace_pattern = re.compile(r"\{([^\}]+)\}")
    xpath_pattern = re.compile(r"xpath:(//[^\s]+)")

    result = []
    current_index = 0

    while current_index < len(input_string):
        # Try to match brace pattern
        brace_match = brace_pattern.match(input_string, current_index)
        if brace_match:
            result.append(("brace", "{" + brace_match.group(1) + "}"))
            current_index = brace_match.end()
            continue

        # Try to match xpath pattern
        xpath_match = xpath_pattern.match(input_string, current_index)
        if xpath_match:
            result.append(("xpath", xpath_match.group(1)))
            current_index = xpath_match.end()
            continue

        # Otherwise, accumulate as a normal string until the next special pattern
        next_special_index = min(
            (
                brace_pattern.search(input_string, current_index).start()
                if brace_pattern.search(input_string, current_index)
                else len(input_string)
            ),
            (
                xpath_pattern.search(input_string, current_index).start()
                if xpath_pattern.search(input_string, current_index)
                else len(input_string)
            ),
        )

        result.append(("str", input_string[current_index:next_special_index]))
        current_index = next_special_index

    return result


def resolve_title(raw_title: str, context: dict[str, Any]) -> str:
    parsed_title = parse_title(raw_title)
    final_string = ""

    for element in parsed_title:
        element_type, element_value = element

        if element_type == "xpath":
            final_string += resolve_xpath(element_value, context["url"])
        elif element_type == "brace":
            final_string += resolve_brace(element_value, context)
        elif element_type == "str":
            final_string += element_value

    return final_string

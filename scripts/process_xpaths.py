import re

import requests
from lxml import etree, html


def is_valid_xpath(xpath):
    try:
        etree.XPath(xpath)
        return True
    except etree.XPathSyntaxError:
        return False


def get_value_from_xpath(url, xpath):
    if not is_valid_xpath(xpath):
        raise ValueError(f"The xpath, {xpath}, is not valid.")

    response = requests.get(url)

    if response.ok:
        tree = html.fromstring(response.content)
        values = tree.xpath(xpath)

        if len(values) == 1:
            text_content = values[0].text
            if text_content:
                return text_content
            else:
                raise ValueError(f"The element at the xpath, {xpath}, does not contain any text content.")
        elif len(values) > 1:
            raise ValueError(f"More than one element found for the xpath, {xpath}")
        else:
            raise ValueError(f"No element found for the xpath, {xpath}")
    else:
        raise ValueError(f"Failed to retrieve the {url}. Status code: {response.status_code}")


def parse_string(input_string):
    # Define regex patterns for each type
    brace_pattern = re.compile(r"\{([^\}]+)\}")
    xpath_pattern = re.compile(r"xpath:(//[^\s]+)")

    # Initialize the result list
    result = []

    # Define the current index
    current_index = 0

    while current_index < len(input_string):
        # Try to match brace pattern
        brace_match = brace_pattern.match(input_string, current_index)
        if brace_match:
            result.append(("brace", brace_match.group(1)))
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


# Example usage
input_string = 'content: {title} xpath://*[@id="centeredcontent2"] overview'
parsed_list = parse_string(input_string)
print(parsed_list)


xpath = '//*[@id="centeredcontent2"]/table[4]/tbody/tr/td/table/tbody/tr/td/table/tbody/tr[2]/td/div/p[1]/text()[1]'

candidate_urls = [
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20021213.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20041209.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20050224.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20050804.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20060223.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20060731_bioDonFreeman.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20060731_bioPaulaGoodman.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20060731_bioThaddeusMiles.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20060731.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20070629_bioKimberlyPaul.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20070629_bioMadelynePfeiffer.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20070629_bioRachelEvans.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcast_20070629.html",
    "https://mars.nasa.gov/imagine/leaders/project_resources/webcasts.html",
]


xpath = '//*[@id="main_content_wrapper"]/h4'
candidate_urls = [
    "https://curator.jsc.nasa.gov/antmet/sample_preparation.cfm?section=cabinet",
    "https://curator.jsc.nasa.gov/antmet/sample_preparation.cfm?section=flowbench",
    "https://curator.jsc.nasa.gov/antmet/sample_preparation.cfm?section=materials",
    "https://curator.jsc.nasa.gov/antmet/sample_preparation.cfm?section=SIprep",
    "https://curator.jsc.nasa.gov/antmet/sample_preparation.cfm?section=thinandthick",
]

for candidate_url in candidate_urls:
    value = get_value_from_xpath(candidate_url, xpath)
    print(f"The value at the specified XPath is: {value}")

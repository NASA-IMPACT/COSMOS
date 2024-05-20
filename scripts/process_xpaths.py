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

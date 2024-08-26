"""Asynchronously scrapes the HTML content of a given URL using a headless browser."""

import asyncio
import re

from bs4 import BeautifulSoup
from pyppeteer import launch


def get_text_table(html_soup):
    """
    Extracts textual content from HTML soup, including table elements.

    Args:
        html_soup (BeautifulSoup): The HTML soup object to extract text from.

    Returns:
        str: The concatenated textual content, including table elements.

    """
    text_content = ""
    count = 0
    for element in html_soup.find_all(string=True):
        if element.parent.name == "table" or count == 0:
            if element.parent.name == "table" and count == 0:
                text_content += str(element.parent) + "\n"
                count = count + 1
            elif element.parent.name == "table" and count != 0:
                count = count - 1
            elif count == 0 and element.parent.name != "table":
                text_content += element.strip() + " "
    return text_content


async def scraper(url):
    """
    Asynchronously scrapes the HTML content of a given URL using a headless browser.

    Args:
        url (str): The URL to scrape.

    Returns:
        tuple: A tuple containing the scraped BeautifulSoup object and
        the extracted text from the HTML content.

    """
    # Launch a headless browser
    browser = await launch()
    # Create a new page
    page = await browser.newPage()
    # Go to the URL
    await page.goto(url)
    # Find all elements on the page
    elements = await page.querySelectorAll("*")
    if elements:
        # Hover over the first element
        await elements[0].hover()
        #         # Wait for a specific duration to allow any dynamic changes to occur
        await asyncio.sleep(1)  # Adjust the duration as
        # Get the HTML content of the hovered element
        html_content = await page.content()
        # Create a BeautifulSoup object
        soup = BeautifulSoup(html_content, "html.parser")
        text = get_text_table(soup)
        text = re.sub(r"\W+", " ", text)
        # Extract the text from the HTML content
        await browser.close()
        return soup, text

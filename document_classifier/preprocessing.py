import asyncio
import re

import pandas as pd
import requests
from bs4 import BeautifulSoup
from Document_Classifier_inference.async_scraper import get_text_table, scraper


class Preprocessor:
    def __init__(self, config, data):
        """
        Initializes a Preprocessor object.

        Args:
            data: The data to be processed.

        """
        self.data = data
        self.config = config
        self.pdf_lists = []
        self.image_lists = []

    @classmethod
    def from_dict(cls, cfg: dict, data):
        """
        Creates an Preprocessor object from a dictionary and data.

        Args:
            cfg (dict): A dictionary containing configuration parameters for the preprocessor.
            data: The data to be encoded.

        Returns:
            Preprocessor: An instance of the Preprocessor class.

        """
        return cls(cfg, data)

    def remove_header_footer(self):
        """
        Removes the header and footer from HTML content in a dataset.

        The method makes HTTP requests to URLs specified in the dataset, retrieves the HTML content,
        and removes the header,footer and title elements from the HTML code.
        """

        self.data["classes"] = self.data["class"]
        data_class = self.data.classes.values
        data_urls = self.data.links.values
        soups, urls, classes = [], [], []
        for enum, each_url in enumerate(data_urls):
            try:
                response = requests.get(each_url)
            except Exception:
                continue
            content_type = response.headers.get("Content-Type")
            if content_type is not None and "image" in content_type:
                self.image_lists.append(each_url)
            elif content_type is not None and "pdf" not in content_type:
                html_page = response.text
                # Parsing the HTML content using BeautifulSoup
                soup = BeautifulSoup(html_page, "html.parser")
                text = get_text_table(soup)
                text = re.sub(r"\W+", " ", text)
                if text == "" or text is None:
                    soup, text = asyncio.get_event_loop().run_until_complete(scraper(each_url))
                result = soup.find("header")
                if result:
                    result.extract()  # removing header element from the HTML code
                result = soup.find("footer")
                if result:
                    result.extract()  # removing footer element from the HTML code
                title = soup.find("title")
                if title:
                    title.extract()  # removing title from HTML response
                soups.append(soup)
                classes.append(data_class[enum])
                urls.append(each_url)
            elif content_type is not None and "pdf" in content_type:
                self.pdf_lists.append(each_url)
            else:
                text = response.text
                html_page = f"<html> {text} </html>"
                soup = BeautifulSoup(html_page, "html.parser")
                soups.append(soup)
                classes.append(data_class[enum])
                urls.append(each_url)
        self.data = pd.DataFrame()
        self.data["soup"] = soups
        self.data["links"] = urls
        self.data["class"] = classes

    def preprocessed_features(self):
        """
        Preprocesses the features of the data by removing header and footer, extracting text
        from HTML content.
        Returns:
            tuple: tuple of pandas.DataFrame (The preprocessed data with columns soup,class and links),
              lists of urls with pdf reponse, and lists of urls with image response.
        """
        self.remove_header_footer()
        self.data["soup"] = self.data["soup"].apply(lambda x: re.sub(r"\W+", " ", get_text_table(x).strip()))
        return self.data, self.pdf_lists, self.image_lists

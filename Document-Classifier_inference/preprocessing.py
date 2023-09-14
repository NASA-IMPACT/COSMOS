from io import BytesIO
import re
import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
from PyPDF2 import PdfReader
from async_scraper import scraper, get_text_table


class Preprocessor:
    def __init__(self, config, data):
        """
        Initializes a Preprocessor object.

        Args:
            data: The data to be processed.

        """
        self.data = data
        self.config = config

    @classmethod
    def from_dict(cls, cfg: dict, data):
        """
        Creates an Encoder object from a dictionary and data.

        Args:
            cfg (dict): A dictionary containing configuration parameters for the encoder.
            data: The data to be encoded.

        Returns:
            Encoder: An instance of the Encoder class.

        """
        return cls(cfg, data)

    def pdf_response(self, url):
        """
        Fetches the PDF content from a given URL and extracts the text from it.

        Args:
            url (str): The URL of the PDF.

        Returns:
            str: The extracted text content from the PDF.

        """
        response = requests.get(url)
        pdf_content = response.content
        pdf_stream = BytesIO(pdf_content)
        pdf = PdfReader(pdf_stream)
        text_content = ""
        for page in pdf.pages:
            page_content = page.extract_text()
            if "  references  " in page_content.lower():
                return text_content
            text_content += page.extract_text()
        return text_content

    # removing header and footer to obtain features from the html response
    def remove_header_footer(self):
        """
        Removes the header and footer from HTML content in a dataset.

        The method makes HTTP requests to URLs specified in the dataset, retrieves the HTML content,
        and removes the header,footer and title elements from the HTML code.

        Returns:
            pandas.DataFrame: The modified dataset after removing header, footer and title.
        """

        self.data["classes"] = self.data["class"]
        classs = self.data.classes.values
        urlss = self.data.links.values
        soups, urls, classes = [], [], []
        for j, i in enumerate(urlss):
            try:
                response = requests.get(i)
            except requests.exceptions.SSLError as e:
                continue
            content_type = response.headers.get("Content-Type")
            if content_type is not None and "image" in content_type:
                continue
            if content_type is not None and "pdf" not in content_type:
                html_page = response.text
                # Parsing the HTML content using BeautifulSoup
                soup = BeautifulSoup(html_page, "html.parser")
                text = get_text_table(soup)
                text = re.sub(r"\W+", " ", text)
                if text == "" or text is None:
                    soup, text = asyncio.get_event_loop().run_until_complete(scraper(i))
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
                classes.append(classs[j])
                urls.append(i)
            elif content_type is not None and "pdf" in content_type:
                text = self.pdf_response(i)
                html_page = f"<html>{text}</html>"
                soup = BeautifulSoup(html_page, "html.parser")
                soups.append(soup)
                classes.append(classs[j])
                urls.append(i)
            else:
                text = response.text
                html_page = f"<html> {text} </html>"
                soup = BeautifulSoup(html_page, "html.parser")
                soups.append(soup)
                classes.append(classs[j])
                urls.append(i)
        self.data = pd.DataFrame()
        self.data["soup"] = soups
        self.data["links"] = urls
        self.data["class"] = classes
        return self.data

    def preprocessed_features(self):
        """
        Preprocesses the features of the data by removing header and footer, extracting text
        from HTML content.
        Returns:
            pandas.DataFrame: The preprocessed data with columns soup,class and links.
        """
        self.remove_header_footer()
        self.data["soup"] = self.data["soup"].apply(
            lambda x: re.sub(r"\W+", " ", get_text_table(x).strip())
        )
        return self.data

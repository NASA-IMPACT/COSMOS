"""
sinequa does not handle redirects well, needed a python script to find the actual url
and any better titles that might be available. this particular script runs on a csv
containing solar urls
"""

import csv
import json

import bs4 as BeautifulSoup
import requests


def csv_to_dict_list(file_path):
    with open(file_path, encoding="utf-8") as file:
        dict_reader = csv.DictReader(file)
        list_of_dicts = list(dict_reader)
    return list_of_dicts


file_path = "solar_urls.csv"
urls = csv_to_dict_list(file_path)


# filter out unwanted urls
# this removes 10.5k / 71k urls
urls = [u for u in urls if "unwanted" not in u["type"]]
urls = [u for u in urls if "contact" not in u["url"]]
urls = [u for u in urls if ".amp" not in u["url"]]


processed_urls = []
for index, url_data in enumerate(urls):
    url = url_data["url"]
    title = url_data["old title"]

    try:
        response = requests.get(url, allow_redirects=True, timeout=5)
        response_url = response.url if response.history else url

        try:
            soup = BeautifulSoup(response.content, "html.parser")
            scraped_title = soup.find("title").text.strip() if soup.find("title") else ""
        except Exception:
            scraped_title = ""
    except Exception:
        response_url = ""
        scraped_title = ""

    processed_urls.append(
        {
            "og_url": url,
            "final_url": response_url,
            "og_title": title,
            "scraped_title": scraped_title,
        }
    )

    if index % 100 == 0:
        print(f"Processed {index} URLs.")
        json.dump(processed_urls, open(f"solar_urls/{index}.json", "w"))
        processed_urls = []

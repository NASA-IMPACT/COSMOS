import csv

import bs4 as BeautifulSoup
import requests
import tqdm


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


url_mappings = []
for url in tqdm(urls[1:]):
    response = requests.get(url, allow_redirects=True)
    url_mappings.append({"original": url, "redirect": response.url})

response_urls = []
response_titles = []
counter = 0
for url in urls:
    try:
        # Send a GET request
        response = requests.get(url, timeout=10)

        response_url = response.url if response.history else url

        try:
            soup = BeautifulSoup(response.content, "html.parser")
            title = soup.find("title").text.strip() if soup.find("title") else ""
        except Exception as parse_error:
            # If parsing fails, log the error and use an empty string as the title
            print(f"Error parsing URL {url}: {parse_error}")
            title = ""

    except requests.RequestException as req_error:
        # In case of a request error, log the URL and the error
        print(f"Request failed for {url}: {req_error}")
        response_url = ""
        title = ""

    # Append the fetched data to the lists
    response_urls.append(response_url)
    response_titles.append(title)

    counter += 1
    # Print the number of URLs processed
    print(f"Processed {counter} URLs.")

import json
import os
from collections import defaultdict
from urllib.parse import urlparse

LOG_FILE_NAME = "sde_scraper.log"

# assuming log file was saved with jsonl format
# {"url": "https://appliedsciences.nasa.gov/", "title": "Homepage | NASA Applied Sciences"}
# {"url": "https://appliedsciences.nasa.gov/our-impact/news", "title": "News | NASA Applied Sciences"}
with open(LOG_FILE_NAME) as scraped_file:
    urls = scraped_file.readlines()

url_list = [json.loads(url) for url in urls]
BASE_URL = urlparse(url_list[0]["url"]).netloc
PROTOCOL = urlparse(url_list[0]["url"]).scheme

url_list_truncated = []

for url in url_list:
    parsed = urlparse(url["url"])
    # query looks like this: ?page=2
    if parsed.query:
        append_url = f"{parsed.path}?{parsed.query}"
    else:
        append_url = parsed.path
    url["url"] = append_url
    url_list_truncated.append(append_url)

my_list = url_list_truncated
my_dict = defaultdict(list)

for item in my_list:
    if os.path.isdir(item):  # To check path is a directory
        _ = my_dict[item]  # will set default value as empty list
    else:
        path, file = os.path.split(item)
        my_dict[path].append(file)


with open("output_file.html", "w") as output_file:
    output_file.write(f"<h1>{BASE_URL}</h1>\n")
    output_file.write("<ul>\n")
    for key, value in my_dict.items():
        output_file.write(f'<li><a href="{PROTOCOL}://{BASE_URL}{key}" target=_blank>{key}</a>\n')  # noqa: E231
        output_file.write("<ul>\n")
        for item in value:
            output_file.write(
                f'<li><a href="{PROTOCOL}://{BASE_URL}{key}/{item}" target=_blank>{item}</a></li>\n'
            )  # noqa: E231
        output_file.write("</ul>\n")
        output_file.write("</li>\n")
    output_file.write("</ul>\n")

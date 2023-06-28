# rename this file to config.py and do not track it on git
# example on how to get the token are in the README.md

from sources_to_scrape import sources_to_scrape_20230616

# API Config
tokens: dict[str, str] = {
    "test_server": "token here",
    "ren_server": "token here",
}

# Job Creation Config
# although we will eventually incorporate job creation seamlessly into the webapp
# for now, when you want to create new jobs, you can configure them here
collection_list: list[str] = sources_to_scrape_20230616
date_of_batch: str = "20230616"
n: int = 5  # number of collections to run in parellel (as well as number of joblists)

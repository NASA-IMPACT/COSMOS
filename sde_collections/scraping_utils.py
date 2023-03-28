import requests
from bs4 import BeautifulSoup

MAX_DEPTH = 5


def recursive_url(url, link, depth):
    if depth == MAX_DEPTH:
        return url
    else:
        page = requests.get(url + link["href"])
        soup = BeautifulSoup(page.text, "html.parser")
        newlink = soup.find("a")
        if len(newlink) == 0:
            return link
        else:
            return link, recursive_url(url, newlink, depth + 1)


def generate_candidate_urls(url):
    """
    Generate candidate urls from a given url.
    """

    page = requests.get(url)
    soup = BeautifulSoup(page.text, "html.parser")
    links = soup.find_all("a")
    for link in links:
        links.append(recursive_url(url, link, 0))
    return list(set(links))


if __name__ == "__main__":
    candidate_urls = generate_candidate_urls("https://www.astromat.org/")
    with open("candidate_urls.txt", "w") as f:
        for url in candidate_urls:
            f.write(url + "\n")

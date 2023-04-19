from generate_logfile_csv import process_logfile_and_generate_csv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from sde_scraper.spiders.base_spider import spider_factory


def run_scraper(name, url):
    """Runs the scraper and generates an output CSV of candidated URLs

    Args:
        name (str): Machine readable name of the collection, from collection.folder
        url (str): collection.url
    """

    # run the scraper
    settings = get_project_settings()
    settings.set("LOG_FILE", f"raw_logfiles/{name}.log")
    settings.set("LOG_LEVEL", "CRITICAL")
    settings.set("LOG_FILE_APPEND", False)
    settings.set("LOG_FORMAT", "%(message)s")

    process = CrawlerProcess(settings)
    process.crawl(spider_factory(name, url))
    process.start()

    # generate the csv
    process_logfile_and_generate_csv(name)

    # add the urls directly to the database
    # TODO

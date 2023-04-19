import argparse

from generate_logfile_csv import process_logfile_and_generate_csv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from sde_scraper.spiders.base_spider import spider_factory

parser = argparse.ArgumentParser(description="Scrapy spider runner.")
parser.add_argument(
    "name", help="Name for the spider configuration, log file, and CSV file."
)
args = parser.parse_args()

name = args.name
logfile_name = name
config_name = name

settings = get_project_settings()
settings.set("LOG_FILE", f"raw_logfiles/{logfile_name}.log")
settings.set("LOG_LEVEL", "CRITICAL")
settings.set("LOG_FILE_APPEND", False)
settings.set("LOG_FORMAT", "%(message)s")

process = CrawlerProcess(settings)
process.crawl(spider_factory(config_name))
process.start()

process_logfile_and_generate_csv(logfile_name)


# if you wanted to loop through the config files, you could use this code
# configs_path = 'config.yaml'
# with open(configs_path, 'r') as file:
#     configs = yaml.safe_load(file)
# source_names = list(configs.keys())

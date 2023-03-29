from generate_logfile_csv import process_logfile_and_generate_csv
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from sde_scraper.spiders.base_spider import spider_factory

process = CrawlerProcess(get_project_settings())
process.crawl(spider_factory("CCMC"))
process.start()

process_logfile_and_generate_csv()


# if you wanted to loop through the config files, you could use this code
# configs_path = 'config.yaml'
# with open(configs_path, 'r') as file:
#     configs = yaml.safe_load(file)
# source_names = list(configs.keys())

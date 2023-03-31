from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

from config import celery_app
from scraper.scraper.spiders.base_spider import spider_factory


@celery_app.task()
def generate_candidate_urls_async(config_folder):
    """Generate candidate urls using celery."""
    process = CrawlerProcess(get_project_settings())
    process.crawl(spider_factory(config_folder))
    process.start()

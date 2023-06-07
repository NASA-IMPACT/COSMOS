# call a test scraper with scrapy crawl base_spider
# call a specifc config example with scrapy crawl base_spider -a source_name=<source_name_from_config_here>

from urllib.parse import urlparse

from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

from sde_collections.models.collection import Collection


def process_possible_list(possible_list):
    return possible_list


def generate_allowed_domains(allowed_domains, start_urls):
    """
    allowed domains are not always specified, and if not, they should be created based on the
    start_url. if there was no value in the config file, then the content passed to this function
    will be empty and will trigger the creation routine
    """

    if not (allowed_domains):
        allowed_domains = [urlparse(d).netloc for d in start_urls]
    else:
        allowed_domains = process_possible_list(allowed_domains)

    return allowed_domains


def generate_deny_extensions(extensions):
    """
    the default extension parameter doesn't always work for stacked extensions.
    so instead, regex denies are used
    """
    extensions = process_possible_list(extensions)
    return [rf".*\.{extension}$" for extension in extensions]


def config_processor(config_folder):
    # raw_config = configs[config_folder]
    collection = Collection.objects.get(config_folder=config_folder)

    start_urls = process_possible_list([collection.url])

    config = {
        "name": config_folder,
        "start_urls": start_urls,
        "allowed_domains": generate_allowed_domains([], start_urls),
        "rules": {
            "deny_extensions": process_possible_list([]),
            "deny": process_possible_list([]),
        },
    }

    return config


def spider_factory(config_folder):
    config = config_processor(config_folder)

    class FactorySpider(CrawlSpider):
        name = "base_spider"

        allowed_domains = config["allowed_domains"]
        start_urls = config["start_urls"]

        rules = (
            Rule(
                LinkExtractor(allow=(".*"), deny=config["rules"]["deny"]),
                callback="parse_item",
                follow=True,
            ),
        )

        def parse_item(self, response):
            yield {
                "url": response.url,
                "title": response.css("title::text").get(),
            }

    return FactorySpider

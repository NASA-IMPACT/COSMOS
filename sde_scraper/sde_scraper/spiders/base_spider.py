# call a test scraper with scrapy crawl base_spider
# call a specifc config example with scrapy crawl base_spider -a source_name=<source_name_from_config_here>

import json
from urllib.parse import urlparse

import yaml
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule

CONFIGS_PATH = "config.yaml"


def process_possible_list(possible_list):
    if possible_list:
        return [item.strip() for item in possible_list.split(",")]


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


def config_processor(configs_path, source_name="test"):
    with open(configs_path) as file:
        configs = yaml.safe_load(file)
    raw_config = configs[source_name]

    start_urls = process_possible_list(raw_config["start_urls"])

    config = {
        "name": source_name,
        "start_urls": start_urls,
        "allowed_domains": generate_allowed_domains(
            raw_config.get("allowed_domains", ""), start_urls
        ),
        "rules": {
            "deny_extensions": process_possible_list(
                raw_config["rules"]["deny_extensions"]
            ),
            "deny": process_possible_list(raw_config["rules"].get("deny")),
        },
    }

    return config


def spider_factory(source_name):
    config = config_processor(CONFIGS_PATH, source_name)

    class FactorySpider(CrawlSpider):
        name = "base_spider"

        allowed_domains = config["allowed_domains"]
        start_urls = config["start_urls"]
        # allowed_domains = ['heasarc.gsfc.nasa.gov']
        # start_urls = ['https://heasarc.gsfc.nasa.gov/docs/heasarc/caldb/']

        rules = (
            Rule(
                LinkExtractor(allow=(".*"), deny=config["rules"]["deny"]),
                callback="parse_item",
                follow=True,
            ),
        )

        # rules = (
        #     Rule(
        #         LinkExtractor(allow=r'heasarc\.gsfc\.nasa\.gov/docs/heasarc/caldb/.*'),
        #         callback='parse_item',
        #         follow=True,
        #     ),
        # )

        def parse_item(self, response):
            info = json.dumps(
                {"url": response.url, "title": response.css("title::text").get()}
            )
            print(info)
            self.logger.critical(info)

    return FactorySpider

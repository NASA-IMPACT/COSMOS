from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class AstropediaSpider(CrawlSpider):
    name = "astropedia"

    allowed_domains = ["astrogeology.usgs.gov"]
    start_urls = ["https://astrogeology.usgs.gov/search?pmi-target=mercury"]

    rules = (
        Rule(
            LinkExtractor(allow=(".*")),
            callback="parse_item",
            follow=True,
        ),
    )

    def parse_item(self, response):
        yield {
            "url": response.url,
            "title": response.css("title::text").get(),
        }

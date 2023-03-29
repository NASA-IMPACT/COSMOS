from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule


class ExoMastSpider(CrawlSpider):
    name = "exomast"

    allowed_domains = ["exo.mast.stsci.edu"]
    start_urls = ["https://exo.mast.stsci.edu/docs/"]

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

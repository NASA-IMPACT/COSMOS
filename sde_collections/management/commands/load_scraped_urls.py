import json
from collections import defaultdict
from urllib.parse import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from sde_collections.models import CandidateURL, Collection


class Command(BaseCommand):
    help = "Load scraped URLs into the database"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tree = lambda: defaultdict(self.tree)
        self.collection = None

    def _make_tree(self, lst):
        d = self.tree()
        for x in lst:
            curr = d
            for item in x:
                curr = curr[item]
        return d

    def _make_bulk_data(self, d, level=0):
        children = []
        for k, v in d.items():
            if not k:
                continue
            children.append(
                {
                    "data": {
                        "url": k,
                        "collection": self.collection.id,
                        "excluded": False,
                    },
                    "children": self._make_bulk_data(v, level + 1),
                }
            )
        return children

    def add_arguments(self, parser):
        parser.add_argument("config_folders", nargs="+", type=str)

    def parse_jsonl(self, items):
        return [urlparse(json.loads(item)["url"]).path.split("/")[1:] for item in items]

    def handle(self, *args, **options):
        SCRAPED_URLS_DIR = f"{settings.BASE_DIR}/scraper/scraped_urls"
        for config_folder in options["config_folders"]:
            try:
                self.collection = Collection.objects.get(config_folder=config_folder)
            except Collection.DoesNotExist:
                raise CommandError(
                    'Collection with config folder "%s" does not exist' % config_folder
                )

            try:
                with open(f"{SCRAPED_URLS_DIR}/{config_folder}/urls.jsonl") as f:
                    urls = f.readlines()
                    for url in urls:
                        candidate_url_dict = json.loads(url)
                        url = candidate_url_dict["url"]
                        parsed = urlparse(url)
                        path = f"{parsed.path}"
                        if parsed.query:
                            path += f"?{parsed.query}"
                        level = path.count("/")

                        title = candidate_url_dict["title"]
                        if not title:
                            title = ""
                        collection_id = self.collection.id
                        collection = Collection.objects.get(id=collection_id)

                        CandidateURL.objects.get_or_create(
                            collection=collection,
                            url=url,
                            scraped_title=title.strip(),
                            level=level,
                        )

            except FileNotFoundError:
                raise CommandError('No scraped URLs found for "%s"' % config_folder)

            self.stdout.write(
                self.style.SUCCESS('Successfully loaded data from "%s"' % config_folder)
            )

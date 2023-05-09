import json
import os

from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models import Collection
from .sinequa_utils import Sinequa
from .tasks import generate_candidate_urls_async


class CollectionTestCase(TestCase):
    def test_import_sinequa_metadata(self):
        sinequa = Sinequa(config_folder="ARSETAppliedSciences")
        self.assertEqual(
            sinequa.fetch_treeroot(),
            "Earth Science/Documents/User Guides and Training/ARSET Applied Sciences/",
        )
        self.assertEqual(
            sinequa.fetch_document_type(),
            Collection.DocumentTypes.DOCUMENTATION,
        )


class GenerateURLsTestCase(TestCase):
    fixtures = [
        "sde_collections/fixtures/collections.json",
    ]

    def test_generate_urls(self):
        config_folder = "ASTRO_exoMAST_API_Website"
        generate_candidate_urls_async(config_folder)

        # test whether folder got created
        self.assertTrue(os.path.exists(f"scraper/scraped_urls/{config_folder}"))

        # test whether urls got created
        self.assertTrue(
            os.path.exists(f"scraper/scraped_urls/{config_folder}/urls.jsonl")
        )

        # test whether url can be read with json
        with open(f"scraper/scraped_urls/{config_folder}/urls.jsonl") as f:
            line = json.loads(f.readlines()[0])

        self.assertEqual(line["url"], "https://exo.mast.stsci.edu/docs/")


class CreateExcludePatternTestCase(TestCase):
    def test_create_exclude_pattern(self):
        factory = APIRequestFactory()
        response = factory.post(
            "/api/create-exclude-pattern", {"title": "new idea"}, format="json"
        )
        self.assertCountEqual(response, "hey")

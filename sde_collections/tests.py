from django.test import TestCase
from rest_framework.test import APIRequestFactory

from .models.collection import Collection
from .tasks import import_candidate_urls_from_api, push_to_github_task


class CreateExcludePatternTestCase(TestCase):
    def test_create_exclude_pattern(self):
        factory = APIRequestFactory()
        response = factory.post(
            "/api/create-exclude-pattern", {"title": "new idea"}, format="json"
        )
        self.assertCountEqual(response, "hey")


class CreateIncludePatternTestCase(TestCase):
    def test_create_include_pattern(self):
        factory = APIRequestFactory()
        response = factory.post(
            "/api/create-include-pattern", {"title": "new idea"}, format="json"
        )
        self.assertCountEqual(response, "hey")


class ImportCandidateURLsTestCase(TestCase):
    def test_import_all_candidate_urls_from_api(self):
        import_candidate_urls_from_api()
        self.assertEqual(1, 1)


class GitHubTestCase(TestCase):
    fixtures = [
        "sde_collections/fixtures/collections.json",
    ]

    def test_push_config_to_github(self):
        collection = Collection.objects.first()
        push_to_github_task([collection.id])
        self.assertEqual(collection.name, "NASA POWER")

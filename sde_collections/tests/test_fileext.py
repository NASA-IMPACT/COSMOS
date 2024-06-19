from django.test import TestCase

from ..models.candidate_url import CandidateURL
from ..models.collection import Collection


class CandidateURLsTestCase(TestCase):
    def setUp(self):
        # Set up non-modified objects used by all test methods
        collection = Collection.objects.create(
            config_folder="test_folder", name="Test Collection", division=1
        )
        CandidateURL.objects.create(
            url="https://example.com/something.jpg", collection=collection
        )

        # Test cases
        self.urls = {
            "https://example.com/path/to/file.jpg": "jpg",  # Standard file extension
            "https://example.com/path/to/file": "html",  # No extension
            "https://example.com/": "html",  # Root directory
            "https://example.com/path/to/": "html",  # Directory
            "https://example.com/path/to/file.jpg?query=123": "jpg",  # URL with query parameters
            "https://example.com/path/to/file.jpeg#anchor": "jpeg",  # URL with anchor
            "https://example.com/path/to/file": "html",  # File without extension
            "https://example.com/path/to/.hiddenfile": "html",  # Hidden file (starts with dot)
            "https://example.com/path/to/.htaccess": "html",  # .htaccess file
        }

        self.candidate_urls = []

        for url in self.urls:
            self.candidate_urls.append(
                CandidateURL.objects.create(url=url, collection=collection)
            )

    def test_url_content(self):
        for candidate_url in self.candidate_urls:
            expected_extension = self.urls[candidate_url.url]
            self.assertEqual(expected_extension, candidate_url.fileext)

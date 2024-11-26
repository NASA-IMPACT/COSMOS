# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_apis.py

import pytest
from rest_framework import status

from sde_collections.models.delta_patterns import (
    DeltaExcludePattern,
    DeltaIncludePattern,
)
from sde_collections.models.delta_url import CuratedUrl
from sde_collections.tests.factories import CollectionFactory, DeltaUrlFactory


@pytest.mark.django_db
class TestApis:
    """Test suite for APIs"""

    # def setup_method(self):
    #     self.curated_api = "/curated-urls-api/{collection.config_folder}"

    def test_curated_url_api(self, client):
        """
        Test that the curated url api retrieves only the included urls
        """
        collection = CollectionFactory()

        delta_url_included = DeltaUrlFactory(
            collection=collection, url="https://example.com/included_page", scraped_title="Original Title"
        )
        # delta_url_excluded = DeltaUrlFactory(
        #     collection=collection, url="https://example.com/excluded_page", scraped_title="Original Title"
        # )

        # curated_url_included = CuratedUrlFactory(
        #     collection=collection, url="https://example.com/included_page", scraped_title="Original Title"
        # )
        # curated_url_excluded = CuratedUrlFactory(
        #     collection=collection, url="https://example.com/excluded_page", scraped_title="Original Title"
        # )

        # Create a pattern to include urls
        pattern_include = DeltaIncludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/included*", match_pattern_type=2
        )
        # Create a pattern to exclude urls
        pattern_exclude = DeltaExcludePattern.objects.create(
            collection=collection, match_pattern="https://example.com/excluded*", match_pattern_type=2
        )

        collection.promote_to_curated()

        curated_url_included = CuratedUrl.objects.get(url=delta_url_included.url)
        # curated_url_excluded = CuratedUrl.objects.get(url=delta_url_excluded.url)

        pattern_include.apply()
        pattern_exclude.apply()

        api_url = f"http://0.0.0.0:8080/curated-urls-api/{collection.config_folder}"
        # response = requests.get(api_url)

        # client = APIClient()
        response = client.get(api_url, HTTP_ACCEPT="application/json")
        data = response.json()
        # print(response)

        assert response.status_code == status.HTTP_200_OK
        assert data.count == 1
        assert data.results[0].url == curated_url_included.url

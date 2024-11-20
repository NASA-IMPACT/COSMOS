# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_import_fulltexts.py

from unittest.mock import patch

import pytest

from sde_collections.models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from sde_collections.tasks import fetch_and_replace_full_text
from sde_collections.tests.factories import CollectionFactory


@pytest.mark.django_db
def test_fetch_and_replace_full_text():
    # Create a test collection
    collection = CollectionFactory()

    # Mock API response
    mock_documents = [
        {"url": "http://example.com/1", "full_text": "Test Text 1", "title": "Test Title 1"},
        {"url": "http://example.com/2", "full_text": "Test Text 2", "title": "Test Title 2"},
    ]

    with patch("sde_collections.sinequa_api.Api.get_full_texts") as mock_get_full_texts:
        mock_get_full_texts.return_value = mock_documents

        # Call the function
        fetch_and_replace_full_text(collection.id, "lrm_dev")

        # Assertions
        assert DumpUrl.objects.filter(collection=collection).count() == 0
        assert DeltaUrl.objects.filter(collection=collection).count() == len(mock_documents)
        assert CuratedUrl.objects.filter(collection=collection).count() == 0

        for doc in mock_documents:
            assert (
                DeltaUrl.objects.filter(collection=collection)
                .filter(
                    url=doc["url"],
                    scraped_text=doc["full_text"],
                )
                .exists()
            )

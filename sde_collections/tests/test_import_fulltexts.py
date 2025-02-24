# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_import_fulltexts.py

from unittest.mock import patch

import pytest
from django.db.models.signals import post_save

from sde_collections.models.collection import create_configs_on_status_change
from sde_collections.models.delta_url import DeltaUrl, DumpUrl
from sde_collections.tasks import fetch_and_replace_full_text
from sde_collections.tests.factories import CollectionFactory


@pytest.fixture
def disconnect_signals():
    # Disconnect the signal before each test
    post_save.disconnect(create_configs_on_status_change, sender="sde_collections.Collection")
    yield
    # Reconnect the signal after each test
    post_save.connect(create_configs_on_status_change, sender="sde_collections.Collection")


@pytest.mark.django_db
def test_fetch_and_replace_full_text(disconnect_signals):
    collection = CollectionFactory(config_folder="test_folder")

    mock_batch = [
        {"url": "http://example.com/1", "full_text": "Test Text 1", "title": "Test Title 1"},
        {"url": "http://example.com/2", "full_text": "Test Text 2", "title": "Test Title 2"},
    ]

    def mock_generator():
        yield (mock_batch, len(mock_batch))

    with patch("sde_collections.sinequa_api.Api.get_full_texts") as mock_get_full_texts, patch(
        "sde_collections.utils.slack_utils.send_detailed_import_notification"
    ):
        mock_get_full_texts.return_value = mock_generator()

        fetch_and_replace_full_text(collection.id, "lrm_dev")

        assert DumpUrl.objects.filter(collection=collection).count() == 0
        assert DeltaUrl.objects.filter(collection=collection).count() == 2


@pytest.mark.django_db
def test_fetch_and_replace_full_text_large_dataset(disconnect_signals):
    """Test processing a large number of records with proper pagination and batching."""
    collection = CollectionFactory(config_folder="test_folder")

    # Create sample data - 20,000 records in total
    def create_batch(start_idx, size):
        return [
            {"url": f"http://example.com/{i}", "full_text": f"Test Text {i}", "title": f"Test Title {i}"}
            for i in range(start_idx, start_idx + size)
        ]

    # Mock the API to return data in batches of 5000 (matching actual API pagination)
    def mock_batch_generator():
        batch_size = 5000
        total_records = 20000

        for start in range(0, total_records, batch_size):
            yield (create_batch(start, min(batch_size, total_records - start)), total_records)

    with patch("sde_collections.sinequa_api.Api.get_full_texts") as mock_get_full_texts, patch(
        "sde_collections.utils.slack_utils.send_detailed_import_notification"
    ):
        mock_get_full_texts.return_value = mock_batch_generator()

        # Execute the task
        result = fetch_and_replace_full_text(collection.id, "lrm_dev")

        # Verify total number of records
        assert DeltaUrl.objects.filter(collection=collection).count() == 20000

        # Verify some random records exist and have correct data
        for i in [0, 4999, 5000, 19999]:  # Check boundaries and middle
            url = DeltaUrl.objects.get(url=f"http://example.com/{i}")
            assert url.scraped_text == f"Test Text {i}"
            assert url.scraped_title == f"Test Title {i}"

        # Verify batch processing worked by checking the success message
        assert "Successfully processed 20000 records" in result

        # Verify no DumpUrls remain (should all be migrated to DeltaUrls)
        assert DumpUrl.objects.filter(collection=collection).count() == 0

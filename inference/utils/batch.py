# inference/utils/batch.py
from dataclasses import dataclass

from django.db.models import QuerySet


@dataclass
class BatchConfig:
    """Configuration for batch processing"""

    batch_size: int = 100  # URLs per batch
    max_text_length: int = 10000  # Max chars for full_text
    timeout: int = 150  # API timeout in seconds


class BatchProcessor:
    """Handles batching of URLs and preparation of data for API"""

    def __init__(self, config: BatchConfig):
        self.config = config

    def prepare_url_data(self, url) -> dict:
        """Prepare single URL data for API"""
        return {
            "url_id": url.id,
            "text": url.scraped_text[: self.config.max_text_length],
            "metadata": {"title": url.scraped_title, "url": url.url},
        }

    def create_batches(self, urls: QuerySet) -> list[list[dict]]:
        """Split URLs into API-friendly batches"""
        batches = []
        current_batch = []

        for url in urls:
            if len(current_batch) >= self.config.batch_size:
                batches.append(current_batch)
                current_batch = []
            current_batch.append(self.prepare_url_data(url))

        if current_batch:
            batches.append(current_batch)

        return batches

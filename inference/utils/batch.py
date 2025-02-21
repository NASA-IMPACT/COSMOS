# inference/utils/batch.py
from collections.abc import Generator, Iterator
from typing import TypedDict

from django.db.models import QuerySet


class URLData(TypedDict):
    """Type for prepared URL data"""

    url_id: int
    text: str
    metadata: dict


class BatchProcessor:
    """Handles batching of URLs and preparation of data for API"""

    def __init__(self, max_batch_text_length: int = 10000):
        """Initialize with maximum text length per batch"""
        self.max_batch_text_length = max_batch_text_length

    def prepare_url_data(self, url) -> URLData:
        """Prepare single URL data for API"""
        return {
            "url_id": url.id,
            "text": url.scraped_text,
            "metadata": {"title": url.scraped_title, "url": url.url},
        }

    def get_text_length(self, url_data: URLData) -> int:
        """Get the length of text content for a URL"""
        return len(url_data["text"])

    def truncate_oversized_url(self, url_data: URLData) -> URLData:
        """Handle a URL that exceeds the maximum batch length"""
        return {**url_data, "text": url_data["text"][: self.max_batch_text_length]}

    def would_exceed_batch_limit(self, current_length: int, new_length: int) -> bool:
        """Check if adding new text would exceed batch limit"""
        return current_length + new_length > self.max_batch_text_length

    def iter_url_batches(self, urls: QuerySet) -> Generator[list[URLData], None, None]:
        """
        Generate batches of URLs based on total text length.
        If a single URL exceeds max length, it will be truncated and placed in its own batch.

        Args:
            urls: QuerySet of URLs to process

        Yields:
            list[URLData]: Batch of prepared URL data
        """
        # Use iterator() to avoid loading all records at once
        url_iterator: Iterator = urls.iterator()

        current_batch: list[URLData] = []
        current_length: int = 0

        try:
            while True:
                # Get next URL or break if done
                try:
                    url = next(url_iterator)
                except StopIteration:
                    if current_batch:
                        yield current_batch
                    break

                # Prepare URL data
                url_data = self.prepare_url_data(url)
                url_length = self.get_text_length(url_data)

                # Handle oversized URLs
                if url_length > self.max_batch_text_length:
                    # Yield current batch if it exists
                    if current_batch:
                        yield current_batch
                        current_batch = []
                        current_length = 0

                    # Yield truncated oversized URL as its own batch
                    yield [self.truncate_oversized_url(url_data)]
                    continue

                # Check if adding URL would exceed text length limit
                if self.would_exceed_batch_limit(current_length, url_length):
                    # Yield current batch and start new one
                    yield current_batch
                    current_batch = []
                    current_length = 0

                # Add URL to current batch
                current_batch.append(url_data)
                current_length += url_length

        finally:
            # Ensure iterator is closed even if there's an error
            if hasattr(url_iterator, "close"):
                url_iterator.close()

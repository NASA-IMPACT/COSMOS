# inference/tests/test_batch.py
# docker-compose -f local.yml run --rm django pytest inference/tests/test_batch.py
from unittest.mock import MagicMock, Mock, patch

import pytest
from django.db.models import QuerySet

from inference.utils.batch import BatchProcessor


class TestBatchProcessor:
    """Tests for the BatchProcessor class"""

    @pytest.fixture
    def processor(self):
        """Returns a BatchProcessor with default settings"""
        return BatchProcessor()

    @pytest.fixture
    def custom_processor(self):
        """Returns a BatchProcessor with custom max batch size"""
        return BatchProcessor(max_batch_text_length=500)

    @pytest.fixture
    def mock_url(self):
        """Returns a mock URL object with basic attributes"""
        url = Mock()
        url.id = 1
        url.scraped_text = "Sample text content"
        url.scraped_title = "Sample Title"
        url.url = "https://example.com/page"
        return url

    @pytest.fixture
    def mock_url_large(self):
        """Returns a mock URL object with large text content"""
        url = Mock()
        url.id = 2
        url.scraped_text = "X" * 12000  # Exceeds default max size
        url.scraped_title = "Large Content Page"
        url.url = "https://example.com/large-page"
        return url

    def test_init_default(self, processor):
        """Test initialization with default parameters"""
        assert processor.max_batch_text_length == 10000

    def test_init_custom(self, custom_processor):
        """Test initialization with custom max_batch_text_length"""
        assert custom_processor.max_batch_text_length == 500

    def test_prepare_url_data(self, processor, mock_url):
        """Test prepare_url_data method formats URL data correctly"""
        data = processor.prepare_url_data(mock_url)

        assert isinstance(data, dict)
        assert data["url_id"] == mock_url.id
        assert data["text"] == mock_url.scraped_text
        assert data["metadata"]["title"] == mock_url.scraped_title
        assert data["metadata"]["url"] == mock_url.url

    def test_get_text_length(self, processor):
        """Test get_text_length calculates text length correctly"""
        url_data = {
            "url_id": 1,
            "text": "Sample text with specific length",
            "metadata": {"title": "Sample", "url": "https://example.com"},
        }

        length = processor.get_text_length(url_data)
        assert length == len(url_data["text"])

    def test_truncate_oversized_url(self, processor):
        """Test truncate_oversized_url method correctly truncates text"""
        text = "X" * 15000
        url_data = {"url_id": 1, "text": text, "metadata": {"title": "Sample", "url": "https://example.com"}}

        truncated = processor.truncate_oversized_url(url_data)

        assert len(truncated["text"]) == processor.max_batch_text_length
        assert truncated["text"] == text[: processor.max_batch_text_length]
        assert truncated["url_id"] == url_data["url_id"]
        assert truncated["metadata"] == url_data["metadata"]

    def test_would_exceed_batch_limit(self, processor):
        """Test would_exceed_batch_limit correctly determines if adding text would exceed or reach limit"""
        # Should not exceed or reach limit
        assert not processor.would_exceed_batch_limit(5000, 4000)
        assert not processor.would_exceed_batch_limit(0, 9999)

        # Should exceed or reach limit
        assert processor.would_exceed_batch_limit(5000, 6000)
        assert processor.would_exceed_batch_limit(10000, 1)

        # Edge cases
        assert processor.would_exceed_batch_limit(0, 10000)  # Exactly at limit - should start new batch
        assert processor.would_exceed_batch_limit(5000, 5000)  # Exactly at limit - should start new batch
        assert processor.would_exceed_batch_limit(5000, 5001)  # Just over limit

    @pytest.mark.parametrize(
        "url_texts,expected_batches",
        [
            # Empty list
            ([], 0),
            # Single URL within limit
            (["Text of 500 chars"], 1),
            # Multiple URLs that fit in one batch
            (["Text1", "Text2", "Text3"], 1),
            # Multiple URLs that require multiple batches
            (["X" * 6000, "X" * 6000], 2),
            # Mix of sizes
            (["X" * 3000, "X" * 3000, "X" * 6000], 2),
        ],
    )
    def test_iter_url_batches_counts(self, processor, url_texts, expected_batches):
        """Test iter_url_batches creates the expected number of batches"""
        # Create mock URLs with the specified text lengths
        mock_urls = []
        for i, text in enumerate(url_texts):
            url = Mock()
            url.id = i + 1
            url.scraped_text = text
            url.scraped_title = f"Title {i+1}"
            url.url = f"https://example.com/page{i+1}"
            mock_urls.append(url)

        # Create a mock QuerySet
        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter(mock_urls)

        # Count the batches
        batches = list(processor.iter_url_batches(mock_queryset))
        assert len(batches) == expected_batches

    def test_iter_url_batches_empty(self, processor):
        """Test handling of empty QuerySet"""
        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([])

        batches = list(processor.iter_url_batches(mock_queryset))
        assert len(batches) == 0

    def test_iter_url_batches_single_url(self, processor, mock_url):
        """Test processing a single URL"""
        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([mock_url])

        batches = list(processor.iter_url_batches(mock_queryset))

        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0]["url_id"] == mock_url.id
        assert batches[0][0]["text"] == mock_url.scraped_text

    def test_iter_url_batches_oversized_url(self, processor, mock_url_large):
        """Test handling of oversized URLs that exceed the batch limit"""
        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([mock_url_large])

        batches = list(processor.iter_url_batches(mock_queryset))

        assert len(batches) == 1
        assert len(batches[0]) == 1
        assert batches[0][0]["url_id"] == mock_url_large.id
        assert len(batches[0][0]["text"]) == processor.max_batch_text_length

    def test_iter_url_batches_multiple_batches(self, processor):
        """Test processing multiple URLs that require multiple batches"""
        # Create URLs with sizes that force multiple batches
        url1 = Mock(id=1, scraped_text="X" * 6000, scraped_title="Title 1", url="https://example.com/1")
        url2 = Mock(id=2, scraped_text="X" * 6000, scraped_title="Title 2", url="https://example.com/2")
        url3 = Mock(id=3, scraped_text="X" * 2000, scraped_title="Title 3", url="https://example.com/3")

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([url1, url2, url3])

        batches = list(processor.iter_url_batches(mock_queryset))

        assert len(batches) == 2
        # First batch should only contain the first URL (6000 chars)
        assert len(batches[0]) == 1
        assert batches[0][0]["url_id"] == 1

        # Second batch should contain the second and third URLs (6000 + 2000 chars)
        assert len(batches[1]) == 2
        assert batches[1][0]["url_id"] == 2
        assert batches[1][1]["url_id"] == 3

    def test_iter_url_batches_mix_normal_and_oversized(self, processor):
        """Test processing a mix of normal and oversized URLs"""
        # Normal URL
        url1 = Mock(id=1, scraped_text="X" * 2000, scraped_title="Title 1", url="https://example.com/1")
        # Oversized URL
        url2 = Mock(id=2, scraped_text="X" * 15000, scraped_title="Title 2", url="https://example.com/2")
        # Another normal URL
        url3 = Mock(id=3, scraped_text="X" * 3000, scraped_title="Title 3", url="https://example.com/3")

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([url1, url2, url3])

        batches = list(processor.iter_url_batches(mock_queryset))

        assert len(batches) == 3

        # First batch should contain just the first URL
        assert len(batches[0]) == 1
        assert batches[0][0]["url_id"] == 1

        # Second batch should contain just the oversized URL, truncated
        assert len(batches[1]) == 1
        assert batches[1][0]["url_id"] == 2
        assert len(batches[1][0]["text"]) == processor.max_batch_text_length

        # Third batch should contain just the third URL
        assert len(batches[2]) == 1
        assert batches[2][0]["url_id"] == 3

    def test_iter_url_batches_boundary_cases(self, processor):
        """Test behavior at the batch size boundary"""
        exact_size = processor.max_batch_text_length
        just_under = exact_size - 1
        just_over = exact_size + 1

        url1 = Mock(id=1, scraped_text="X" * just_under, scraped_title="Title 1", url="https://example.com/1")
        url2 = Mock(id=2, scraped_text="X" * 1, scraped_title="Title 2", url="https://example.com/2")  # Just 1 char
        url3 = Mock(id=3, scraped_text="X" * just_over, scraped_title="Title 3", url="https://example.com/3")

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([url1, url2, url3])

        batches = list(processor.iter_url_batches(mock_queryset))

        assert len(batches) == 3

        # First batch should contain just url1 (just under limit)
        assert len(batches[0]) == 1
        assert batches[0][0]["url_id"] == 1

        # Second batch should contain just url2 (couldn't fit with url1)
        assert len(batches[1]) == 1
        assert batches[1][0]["url_id"] == 2

        # Third batch should contain url3 truncated (over limit)
        assert len(batches[2]) == 1
        assert batches[2][0]["url_id"] == 3
        assert len(batches[2][0]["text"]) == processor.max_batch_text_length

    def test_iterator_is_closed(self, processor):
        """Test that the URL iterator is properly closed"""

        # Create a proper iterator class with close method
        class MockIterator:
            def __iter__(self):
                return self

            def __next__(self):
                raise StopIteration()  # Empty iterator

            def close(self):
                pass  # Do nothing but allow tracking

        # Create the iterator and spy on close
        mock_iterator = MockIterator()
        mock_iterator.close = MagicMock()  # Replace with mockable version

        # Create a mock QuerySet that returns our mock_iterator
        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = mock_iterator

        # Consume the generator
        list(processor.iter_url_batches(mock_queryset))

        # Verify close was called
        mock_iterator.close.assert_called_once()

    def test_iterator_error_handling(self, processor):
        """Test that errors during iteration are handled properly"""

        # Create a proper iterator that raises after first item
        class FailingIterator:
            def __init__(self):
                self.has_yielded = False

            def __iter__(self):
                return self

            def __next__(self):
                if not self.has_yielded:
                    self.has_yielded = True
                    return Mock(id=1, scraped_text="Text", scraped_title="Title", url="https://example.com")
                raise ValueError("Test exception")

            def close(self):
                pass  # Do nothing but allow tracking

        # Create the iterator and spy on close
        mock_iterator = FailingIterator()
        mock_iterator.close = MagicMock()  # Replace with mockable version

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = mock_iterator

        # The generator should propagate the exception but still close the iterator
        with pytest.raises(ValueError):
            list(processor.iter_url_batches(mock_queryset))

        # Verify close was still called despite the exception
        mock_iterator.close.assert_called_once()

    def test_integration_with_mock_django_db(self, processor):
        """Test integration with mocked Django DB objects"""
        from sde_collections.tests.factories import DumpUrlFactory

        # Create a patch for the QuerySet iterator that returns our factory objects
        with patch.object(QuerySet, "iterator") as mock_iterator:
            # Create mock URLs using the factory
            url1 = DumpUrlFactory.build(id=1, scraped_text="Text 1")
            url2 = DumpUrlFactory.build(id=2, scraped_text="Text 2")

            # Set up the mock to return these objects
            mock_iterator.return_value = iter([url1, url2])

            # Create a real QuerySet (that will use our mock iterator)
            mock_queryset = MagicMock(spec=QuerySet)
            mock_queryset.iterator = mock_iterator

            # Process the batches
            batches = list(processor.iter_url_batches(mock_queryset))

            # Verify the output
            assert len(batches) == 1  # Both URLs fit in one batch
            assert len(batches[0]) == 2
            assert batches[0][0]["url_id"] == 1
            assert batches[0][1]["url_id"] == 2


# Additional test class to identify potential issues
class TestBatchProcessorPotentialIssues:
    """Tests focused on identifying potential problems with BatchProcessor"""

    def test_extremely_large_text(self):
        """Test handling of extremely large text to check for memory issues"""
        processor = BatchProcessor()

        # Create a URL with extremely large text (100MB)
        # This is simulated rather than actually creating such a large string
        large_text_size = 100 * 1024 * 1024  # 100MB

        url = Mock()
        url.id = 1

        # Instead of creating a huge string, we'll patch get_text_length
        # to simulate the size calculation
        with patch.object(processor, "get_text_length", return_value=large_text_size):
            url_data = {"url_id": url.id, "text": "LARGE", "metadata": {}}

            with patch.object(processor, "prepare_url_data", return_value=url_data):
                mock_queryset = MagicMock(spec=QuerySet)
                mock_queryset.iterator.return_value = iter([url])

                batches = list(processor.iter_url_batches(mock_queryset))

                # Should create a single batch with truncated content
                assert len(batches) == 1
                assert len(batches[0]) == 1

    def test_url_with_no_text(self):
        """Test handling of URLs with empty text"""
        processor = BatchProcessor()

        url = Mock(id=1, scraped_text="", scraped_title="Empty Text", url="https://example.com/empty")

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([url])

        batches = list(processor.iter_url_batches(mock_queryset))

        # Should still create a batch even with empty text
        assert len(batches) == 1
        assert batches[0][0]["text"] == ""

    def test_url_with_none_text(self):
        """Test handling of URLs with None text"""
        processor = BatchProcessor()

        url = Mock(id=1, scraped_text=None, scraped_title="None Text", url="https://example.com/none")

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([url])

        # This should not raise a TypeError when calculating text length
        batches = list(processor.iter_url_batches(mock_queryset))

        # Should create a batch with "None" text converted to string
        assert len(batches) == 1
        assert batches[0][0]["text"] is not None
        assert batches[0][0]["text"] == ""

    def test_missing_required_fields(self):
        """Test handling of URLs missing required fields"""
        processor = BatchProcessor()

        # URL missing scraped_text
        incomplete_url = Mock(spec=["id", "url", "scraped_title"])
        incomplete_url.id = 1
        incomplete_url.scraped_title = "Missing Text"
        incomplete_url.url = "https://example.com/incomplete"
        # No attribute for scraped_text

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = iter([incomplete_url])

        # Should raise AttributeError when trying to access missing attribute
        with pytest.raises(AttributeError):
            list(processor.iter_url_batches(mock_queryset))

    def test_iterator_without_close_method(self):
        """Test graceful handling of iterators without close method"""
        processor = BatchProcessor()

        # Create a simple list iterator without a close method
        simple_iterator = iter([Mock(id=1, scraped_text="Text", scraped_title="Title", url="https://example.com")])

        mock_queryset = MagicMock(spec=QuerySet)
        mock_queryset.iterator.return_value = simple_iterator

        # Should not raise AttributeError when trying to close the iterator
        batches = list(processor.iter_url_batches(mock_queryset))
        assert len(batches) == 1

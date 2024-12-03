# docker-compose -f local.yml run --rm django pytest sde_collections/tests/test_title_resolution.py

from unittest.mock import Mock, patch

import pytest

from ..utils.title_resolver import (
    clean_text,
    is_valid_xpath,
    parse_title,
    resolve_brace,
    resolve_title,
    resolve_xpath,
    validate_fstring,
)


def test_parse_title():
    # Test basic string
    assert parse_title("Simple Title") == [("str", "Simple Title")]

    # Test f-string
    assert parse_title("Hello {title}") == [("str", "Hello "), ("brace", "{title}")]

    # Test xpath
    assert parse_title("xpath://h1") == [("xpath", "//h1")]

    # Test complex pattern
    result = parse_title("xpath://h1 | {title} - {collection}")
    assert result == [
        ("xpath", "//h1"),
        ("str", " | "),
        ("brace", "{title}"),
        ("str", " - "),
        ("brace", "{collection}"),
    ]


def test_is_valid_xpath():
    assert is_valid_xpath("//h1") is True
    assert is_valid_xpath("//div[@class='title']") is True
    assert is_valid_xpath("invalid xpath") is False
    assert is_valid_xpath("//h1[") is False


def test_validate_fstring():
    # Valid cases - should not raise
    validate_fstring("{title}")
    validate_fstring("{url}")
    validate_fstring("{collection}")

    # Invalid cases
    with pytest.raises(ValueError):
        validate_fstring("{invalid_var}")
    with pytest.raises(ValueError):
        validate_fstring("{title.upper()}")
    with pytest.raises(ValueError):
        validate_fstring("{len(title)}")


def test_resolve_brace():
    context = {"title": "Test Title", "url": "https://example.com", "collection": "Test Collection"}

    assert resolve_brace("{title}", context) == "Test Title"
    assert resolve_brace("{title} - {collection}", context) == "Test Title - Test Collection"

    with pytest.raises(ValueError):
        resolve_brace("{invalid}", context)


def test_clean_text():
    # Test whitespace handling
    assert clean_text("  Title  \n  With\tSpaces  ") == "Title With Spaces"

    # Test HTML entities
    assert clean_text("Title &amp; More") == "Title & More"

    # Test unicode normalization
    assert clean_text("Café") == "Cafe"


@patch("requests.get")
def test_resolve_xpath(mock_get):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.content = b"""
        <html>
            <body>
                <h1>Test Title</h1>
                <div class="content">Inner Content</div>
            </body>
        </html>
    """
    mock_get.return_value = mock_response

    # Test basic xpath
    assert resolve_xpath("//h1", "https://example.com") == "Test Title"
    assert resolve_xpath("//div[@class='content']", "https://example.com") == "Inner Content"

    # Test error cases
    mock_response.ok = False
    with pytest.raises(ValueError):
        resolve_xpath("//h1", "https://example.com")

    mock_response.ok = True
    with pytest.raises(ValueError):
        resolve_xpath("//nonexistent", "https://example.com")


@patch("requests.get")
def test_resolve_title(mock_get):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.content = b"""
        <html>
            <body>
                <h1>Dynamic Content</h1>
            </body>
        </html>
    """
    mock_get.return_value = mock_response

    context = {"title": "Original Title", "url": "https://example.com", "collection": "Test Collection"}

    # Test combination of xpath and f-string
    pattern = "xpath://h1 | {title} - {collection}"
    assert resolve_title(pattern, context) == "Dynamic Content | Original Title - Test Collection"

    # Test simple f-string
    assert resolve_title("{title} ({collection})", context) == "Original Title (Test Collection)"

    # Test plain string
    assert resolve_title("Static Title", context) == "Static Title"

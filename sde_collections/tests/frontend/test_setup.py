from .base import BaseTestCase


class TestSetup(BaseTestCase):
    """Verify Selenium setup is working correctly."""

    def test_basic_page_load(self):
        """Test that we can load a page."""
        # Print the live server URL
        print(f"\nTest server running at: {self.live_server_url}")

        self.driver.get(self.live_server_url)
        print(f"Current URL: {self.driver.current_url}")
        print(f"Page Title: {self.driver.title}")

        assert self.driver.title == "Sign In | COSMOS"

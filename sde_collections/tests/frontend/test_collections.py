from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import CollectionFactory, UserFactory
from .base import BaseTestCase


class TestCollections(BaseTestCase):
    """Test collection-related functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        # Create test user and collections
        self.user = UserFactory(is_staff=True)
        self.user.set_password("test_password123")
        self.user.save()

        # Create 3 test collections
        self.collections = [CollectionFactory(curated_by=self.user) for _ in range(3)]
        # Store collection names for verification
        self.collection_names = [collection.name for collection in self.collections]

    def test_collections_display(self):
        """Test that collections are displayed after login."""
        # Login
        self.login(self.user.username, "test_password123")

        # Navigate to collections page
        self.driver.get(f"{self.live_server_url}/")

        # Print page source for debugging
        # print(f"\nCurrent URL: {self.driver.current_url}")
        print(f"Page Source: {self.driver.page_source}")

        # Wait for specific table to load using ID
        table = self.wait.until(EC.presence_of_element_located((By.ID, "collection_table")))

        # Additional verification that it's the right table
        assert "table-striped dataTable" in table.get_attribute("class")

        # Print debug info
        print(f"\nCurrent URL: {self.driver.current_url}")
        print(f"Table HTML: {table.get_attribute('outerHTML')}")

        # Get all table text
        table_text = table.text

        # Verify each collection name is present
        for collection_name in self.collection_names:
            assert collection_name in table_text, f"Collection '{collection_name}' not found in table"
            print(f"Found collection: {collection_name}")

    def tearDown(self):
        """Clean up test data."""
        super().tearDown()

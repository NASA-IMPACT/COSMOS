# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/frontend/test_collections.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import CollectionFactory
from .base import BaseTestCase


class TestHomepageFeatures(BaseTestCase):
    """Test features available in COSMOS Homepage"""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.user, self.password = self.create_test_user(is_staff=True)

        # Create 3 test collections
        self.collections = [CollectionFactory(curated_by=self.user) for _ in range(3)]
        self.collection_names = [collection.name for collection in self.collections]

        self.login(self.user.username, self.password)

    def test_collections_display(self):
        """Test that collections are displayed after login."""
        # Navigate to collections page
        self.driver.get(f"{self.live_server_url}/")

        # Wait for specific table to load using ID
        table = self.wait.until(EC.presence_of_element_located((By.ID, "collection_table")))
        assert "table-striped dataTable" in table.get_attribute("class")

        # Verify each collection name is present
        table_text = table.text
        for collection_name in self.collection_names:
            assert collection_name in table_text, f"Collection '{collection_name}' not found in table"

    def test_universal_search(self):
        """Test universal search functionality."""

        self.driver.get(f"{self.live_server_url}/")
        # Wait for search input and enter search term
        search_input = self.wait.until(EC.presence_of_element_located((By.ID, "collectionSearch")))
        search_input.send_keys(self.collections[0].name)  # Search for first collection

        # Wait for table to update
        table = self.wait.until(EC.presence_of_element_located((By.ID, "collection_table")))

        # Verify search results
        table_text = table.text
        assert self.collections[0].name in table_text, "Target collection should be present"
        assert self.collections[1].name not in table_text, "Collection #2 should not be present"
        assert self.collections[2].name not in table_text, "Collection #3 should not be present"

    def tearDown(self):
        """Clean up test data."""
        super().tearDown()

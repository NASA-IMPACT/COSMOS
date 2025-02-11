# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/frontend/test_collections.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import CollectionFactory
from .base import BaseTestCase


class TestCollections(BaseTestCase):
    """Test collection-related functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()
        self.user, self.password = self.create_test_user(is_staff=True)

        # Create 3 test collections
        self.collections = [CollectionFactory(curated_by=self.user) for _ in range(3)]
        self.collection_names = [collection.name for collection in self.collections]

    def test_collections_display(self):
        """Test that collections are displayed after login."""
        self.login(self.user.username, self.password)

        # Navigate to collections page
        self.driver.get(f"{self.live_server_url}/")

        # Wait for specific table to load using ID
        table = self.wait.until(EC.presence_of_element_located((By.ID, "collection_table")))
        assert "table-striped dataTable" in table.get_attribute("class")

        # Verify each collection name is present
        table_text = table.text
        for collection_name in self.collection_names:
            assert collection_name in table_text, f"Collection '{collection_name}' not found in table"

    def tearDown(self):
        """Clean up test data."""
        super().tearDown()

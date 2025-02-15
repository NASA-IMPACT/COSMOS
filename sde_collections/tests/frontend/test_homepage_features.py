# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/frontend/test_homepage_features.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import (
    CollectionFactory,
    CuratedUrlFactory,
    DeltaUrlFactory,
    UserFactory,
)
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


class TestSearchPaneFeatures(BaseTestCase):
    """Test search pane features on homepage"""

    def setUp(self):
        super().setUp()
        self.user, self.password = self.create_test_user(is_staff=True)
        self.second_test_user = UserFactory()
        self.third_test_user = UserFactory()

        # Create collections with diverse attributes
        self.collections = [
            CollectionFactory(curated_by=self.user, division=1, workflow_status=3, connector=1, reindexing_status=1),
            CollectionFactory(
                curated_by=self.second_test_user, division=3, workflow_status=1, connector=1, reindexing_status=2
            ),
            CollectionFactory(
                curated_by=self.third_test_user, division=4, workflow_status=3, connector=2, reindexing_status=4
            ),
        ]

        # Factory sometimes struggle to generate unique URLs by itself, so applying this technique
        self.delta_urls = []
        self.curated_urls = []
        for i, collection in enumerate(self.collections):
            num_urls = 10**i  # 1, 10, 100, ...
            self.delta_urls.extend(
                [
                    DeltaUrlFactory(collection=collection, url=f"https://example-{collection.id}-{j}.com")
                    for j in range(num_urls)
                ]
            )
            self.curated_urls.extend(
                [
                    CuratedUrlFactory(collection=collection, url=f"https://example-{collection.id}-{j}.com")
                    for j in range(num_urls)
                ]
            )

        self.login(self.user.username, self.password)
        self.driver.get(f"{self.live_server_url}/")
        self.COLUMNS = self.driver.execute_script("return COLUMNS;")

    def test_division_searchpane(self):
        """Test division search pane filtering"""

        # Find and click Astrophysics option
        astrophysics_option = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.dtsp-name[title='Astrophysics']"))
        )
        astrophysics_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows Astrophysics division
        for row in rows:
            division_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["DIVISION"]]
            assert division_cell.text.lower() == "astrophysics", f"Expected Astrophysics but found {division_cell.text}"

    def test_delta_urls_searchpane(self):
        """Test Delta URLs search pane filtering"""

        # Find the Delta URLs pane using its index and then find the "1 solo URL" option within it
        search_panes = self.driver.find_elements(By.CSS_SELECTOR, "div.dtsp-searchPane")
        delta_urls_pane = search_panes[self.COLUMNS["DELTA_URLS"]]
        delta_url_option = delta_urls_pane.find_element(By.CSS_SELECTOR, "span.dtsp-name[title='1 solo URL']")
        delta_url_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows "1" in Delta URLs column
        for row in rows:
            delta_urls_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["DELTA_URLS"]]
            assert delta_urls_cell.text == "1", f"Expected '1' but found {delta_urls_cell.text}"

    def test_curated_urls_searchpane(self):
        """Test Curated URLs search pane filtering"""

        # Find the Curated URLs pane using its index and then find the "1 to 100 URLs" option within it
        search_panes = self.driver.find_elements(By.CSS_SELECTOR, "div.dtsp-searchPane")
        curated_urls_pane = search_panes[self.COLUMNS["CURATED_URLS"]]
        curated_url_option = curated_urls_pane.find_element(By.CSS_SELECTOR, "span.dtsp-name[title='1 to 100 URLs']")
        curated_url_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows a number between 1 and 100 in Curated URLs column
        for row in rows:
            curated_urls_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["CURATED_URLS"]]
            url_count = int(curated_urls_cell.text)
            assert 1 < url_count <= 100, f"Expected number between 1 and 100 but found {url_count}"

    def test_workflow_status_searchpane(self):
        """Test Workflow Status search pane filtering"""

        # Find and click the option with "Engineering in Progress" button
        workflow_status_option = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='dtsp-nameCont']//button[text()='Engineering in Progress']")
            )
        )
        workflow_status_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows "ENGINEERING IN PROGRESS" in Workflow Status column
        for row in rows:
            workflow_status_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["WORKFLOW_STATUS"]]
            assert (
                workflow_status_cell.text.lower() == "engineering in progress"
            ), f"Expected 'ENGINEERING IN PROGRESS' but found {workflow_status_cell.text}"

    def test_curator_searchpane(self):
        """Test Curator search pane filtering"""

        # Find and click the option with "test_user" button
        curator_option = self.wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@class='dtsp-nameCont']//button[text()='test_user']"))
        )
        curator_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows "test_user" in Curator column
        for row in rows:
            curator_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["CURATOR"]]
            assert curator_cell.text.lower() == "test_user", f"Expected 'test_user' but found {curator_cell.text}"

    def test_connector_type_searchpane(self):
        """Test Connector Type search pane filtering"""

        # Find and click "crawler2" option
        crawler2_option = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span.dtsp-name[title='crawler2']"))
        )
        crawler2_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows "crawler2" connector type
        for row in rows:
            connector_type_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["CONNECTOR_TYPE"]]
            assert (
                connector_type_cell.text.lower() == "crawler2"
            ), f"Expected 'crawler2' but found {connector_type_cell.text}"

    def test_reindexing_status_searchpane(self):
        """Test Reindexing Status search pane filtering"""

        # Find and click the option with "Re-Indexing Not Needed" button
        reindexing_option = self.wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='dtsp-nameCont']//button[text()='Re-Indexing Not Needed']")
            )
        )
        reindexing_option.click()

        # Get all rows from the filtered table
        rows = self.driver.find_elements(By.CSS_SELECTOR, "#collection_table tbody tr")
        assert len(rows) > 0, "No rows found after filtering"

        # Verify each row shows "RE-INDEXING NOT NEEDED" in Reindexing Status column
        for row in rows:
            reindexing_status_cell = row.find_elements(By.TAG_NAME, "td")[self.COLUMNS["REINDEXING_STATUS"]]
            assert (
                reindexing_status_cell.text.lower() == "re-indexing not needed"
            ), f"Expected 'RE-INDEXING NOT NEEDED' but found {reindexing_status_cell.text}"

    def tearDown(self):
        """Clear all filters after each test"""

        clear_all_button = self.driver.find_element(By.CSS_SELECTOR, "button.dtsp-clearAll")
        if "disabled" not in clear_all_button.get_attribute("class"):
            clear_all_button.click()
        super().tearDown()

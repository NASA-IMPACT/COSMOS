# docker-compose -f local.yml run --rm django pytest -s sde_collections/tests/frontend/test_pattern_application.py

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import CollectionFactory, CuratedUrlFactory, DeltaUrlFactory
from .base import BaseTestCase


class TestPatternApplication(BaseTestCase):
    """Test different types of pattern application"""

    def setUp(self) -> None:
        super().setUp()
        self.user, self.password = self.create_test_user(is_staff=True)

        self.collection = CollectionFactory(curated_by=self.user)

        self.delta_urls = [
            DeltaUrlFactory(collection=self.collection, url="https://example.com/docs/page1.html"),
            DeltaUrlFactory(collection=self.collection, url="https://example.com/docs/page2.html"),
        ]

        self.curated_urls = [
            CuratedUrlFactory(collection=self.collection, url="https://example.com/docs/page3.html"),
            CuratedUrlFactory(collection=self.collection, url="https://example.com/index.html"),
        ]

        self.login(self.user.username, self.password)
        self.driver.get(f"{self.live_server_url}/{self.collection.id}/delta-urls")

    def test_create_exclude_pattern(self):
        """Test creating a new exclude pattern."""
        # Click Exclude Patterns tab
        exclude_patterns_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "excludePatternsTab")))
        exclude_patterns_tab.click()

        # Click Add Pattern button
        add_pattern_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.addPattern[aria-controls='exclude_patterns_table']"))
        )
        add_pattern_button.click()

        # Fill up the form using JavaScript and close modal properly
        self.driver.execute_script("""
            document.querySelector("#excludePatternModal #match_pattern_input").value = 'example.com/docs/';
            document.querySelector('#excludePatternModal .pattern_type_form_select[value="2"]').click();
            document.querySelector("#excludePatternModal button.btn-primary[type='submit']").click();
        """)

        # Verify pattern details
        pattern_row = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'example.com/docs/')]"))
        )
        row_text = pattern_row.find_element(By.XPATH, "..").text

        assert "example.com/docs/" in row_text
        assert "Multi-URL Pattern" in row_text
        assert "3" in row_text

        self.driver.get(f"{self.live_server_url}/{self.collection.id}/delta-urls")

        # Verify exclude checkmark for each delta URL
        for delta_url in self.delta_urls:
            row = self.driver.find_element(By.ID, delta_url.url)
            check_icon = row.find_element(By.CSS_SELECTOR, "i[style*='color: green']")
            assert check_icon.text == "check"

    def test_create_include_pattern(self):
        """Test creating a new include pattern."""
        # Click Include Patterns tab
        include_patterns_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "includePatternsTab")))
        include_patterns_tab.click()

        # Click Add Pattern button
        add_pattern_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.addPattern[aria-controls='include_patterns_table']"))
        )
        add_pattern_button.click()

        # Fill up the form using JavaScript and close modal properly
        self.driver.execute_script("""
            document.querySelector("#includePatternModal #match_pattern_input").value = 'example.com/docs/';
            document.querySelector('#includePatternModal .pattern_type_form_select[value="2"]').click();
            document.querySelector("#includePatternModal button.btn-primary[type='submit']").click();
        """)

        # Verify pattern details
        pattern_row = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'example.com/docs/')]"))
        )
        row_text = pattern_row.find_element(By.XPATH, "..").text

        assert "example.com/docs/" in row_text
        assert "Multi-URL Pattern" in row_text
        assert "3" in row_text

        self.driver.get(f"{self.live_server_url}/{self.collection.id}/delta-urls")

        # Verify no exclude checkmark for each delta URL
        for delta_url in self.delta_urls:
            row = self.driver.find_element(By.ID, delta_url.url)
            check_icon = row.find_element(By.CSS_SELECTOR, "i[style*='color: red']")
            assert check_icon.text == "close"

    def test_create_title_pattern(self):
        """Test creating a new title pattern."""
        # Click Title Patterns tab
        title_patterns_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "titlePatternsTab")))
        title_patterns_tab.click()

        # Click Add Pattern button
        add_pattern_button = self.wait.until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button.addPattern[aria-controls='title_patterns_table']"))
        )
        add_pattern_button.click()

        # Fill up the form using JavaScript and close modal properly
        self.driver.execute_script("""
            document.querySelector("#titlePatternModal #match_pattern_input").value = 'example.com/docs/';
            document.querySelector("#titlePatternModal #title_pattern_input").value = 'Documentation: {title}';
            document.querySelector('#titlePatternModal .pattern_type_form_select[value="2"]').click();
            document.querySelector("#titlePatternModal button.btn-primary[type='submit']").click();
        """)

        # Verify pattern details
        pattern_row = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'example.com/docs/')]"))
        )
        row_text = pattern_row.find_element(By.XPATH, "..").text

        assert "example.com/docs/" in row_text
        assert "Documentation: {title}" in row_text
        assert "Multi-URL Pattern" in row_text
        assert "3" in row_text

        self.driver.get(f"{self.live_server_url}/{self.collection.id}/delta-urls")

        # Wait for at least one row to be present in the table
        self.wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#delta_urls_table tbody tr td:not(.dt-empty)"))
        )

        table_html = self.driver.find_element(By.ID, "delta_urls_table").get_attribute("outerHTML")

        # Verify that previous curated_url now appear in delta_urls page after pattern application
        assert "example.com/docs/page3.html" in table_html

        # Verify each delta URL's title has been updated with the pattern
        for delta_url in self.collection.delta_urls.all():
            expected_title = f"Documentation: {delta_url.scraped_title}"
            assert expected_title in table_html, f"Expected title '{expected_title}' not found in table"

    def test_create_documenttype_pattern(self):
        """Test creating a new document type pattern."""
        # Click Document Type Patterns tab
        documenttype_patterns_tab = self.wait.until(EC.element_to_be_clickable((By.ID, "documentTypePatternsTab")))
        documenttype_patterns_tab.click()

        # Click Add Pattern button
        add_pattern_button = self.wait.until(
            EC.element_to_be_clickable(
                (By.CSS_SELECTOR, "button.addPattern[aria-controls='document_type_patterns_table']")
            )
        )
        add_pattern_button.click()

        # Fill up the form using JavaScript and close modal properly
        self.driver.execute_script("""
            document.querySelector("#documentTypePatternModal #match_pattern_input").value = 'example.com/docs/';
            document.querySelector('#documentTypePatternModal .document_type_form_select[value="2"]').click();  // DATA
            document.querySelector('#documentTypePatternModal .pattern_type_form_select[value="2"]').click();
            document.querySelector("#documentTypePatternModal button.btn-primary[type='submit']").click();
        """)

        # Verify pattern details
        pattern_row = self.wait.until(
            EC.presence_of_element_located((By.XPATH, "//td[contains(text(), 'example.com/docs/')]"))
        )
        row_text = pattern_row.find_element(By.XPATH, "..").text

        assert "example.com/docs/" in row_text
        assert "Multi-URL Pattern" in row_text
        assert "3" in row_text

        self.driver.get(f"{self.live_server_url}/{self.collection.id}/delta-urls")

        # Verify document type is set to Data
        for delta_url in self.delta_urls:
            row = self.driver.find_element(By.ID, delta_url.url)
            doc_type_button = row.find_element(By.CSS_SELECTOR, "button.btn-success")
            assert doc_type_button.text == "DATA"

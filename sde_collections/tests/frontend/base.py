import shutil
import subprocess

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


class BaseTestCase(StaticLiveServerTestCase):
    """Base class for all frontend tests using Selenium."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Verify ChromeDriver is available
        chromedriver_path = shutil.which("chromedriver")
        if not chromedriver_path:
            pytest.fail("ChromeDriver not found. Please ensure chromium-driver is installed.")

        # # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = "/usr/bin/chromium"

        try:
            # Create service with explicit path
            service = Service(executable_path=chromedriver_path, log_path="/tmp/chromedriver.log")

            # Initialize WebDriver with service and options
            cls.driver = webdriver.Chrome(service=service, options=chrome_options)

            cls.driver.set_window_size(1920, 1080)
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 10)

        except Exception as e:
            # Print debugging information
            subprocess.run(["which", "chromium"])
            subprocess.run(["which", "chromedriver"])
            subprocess.run(["chromium", "--version"])
            subprocess.run(["chromedriver", "--version"])
            pytest.fail(f"Failed to initialize ChromeDriver: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()
        super().tearDownClass()

    def setUp(self):
        """Set up test case."""
        super().setUp()
        # Add any additional setup here

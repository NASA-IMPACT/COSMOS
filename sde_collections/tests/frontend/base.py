import shutil

import pytest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

from .mixins import AuthenticationMixin


class BaseTestCase(StaticLiveServerTestCase, AuthenticationMixin):
    """Base class for all frontend tests using Selenium."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Verify ChromeDriver and Chromium are available
        chromedriver_path = shutil.which("chromedriver")
        chromium_path = shutil.which("chromium")

        if not chromedriver_path:
            pytest.fail("ChromeDriver not found. Please ensure chromium-driver is installed.")
        if not chromium_path:
            pytest.fail("Chromium not found. Please ensure chromium is installed.")

        # Set up Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.binary_location = chromium_path

        try:
            service = Service(executable_path=chromedriver_path)
            cls.driver = webdriver.Chrome(service=service, options=chrome_options)
            cls.driver.set_window_size(1920, 1080)
            cls.driver.implicitly_wait(10)
            cls.wait = WebDriverWait(cls.driver, 10)

        except Exception as e:
            pytest.fail(f"Failed to initialize ChromeDriver: {str(e)}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()
        super().tearDownClass()

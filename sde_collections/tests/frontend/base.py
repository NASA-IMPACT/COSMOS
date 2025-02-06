import shutil
import subprocess

import pytest
from django.contrib.auth import get_user_model
from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
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

    def create_test_user(self, username="test_user", password="test_password123", **kwargs):
        """Create a test user for login testing."""
        User = get_user_model()

        # Delete user if it already exists
        User.objects.filter(username=username).delete()

        user_data = {
            "username": username,
            "is_active": True,
            "is_staff": True,  # Ensure user is staff
            "is_superuser": False,  # Ensure user is superuser
        }
        user_data.update(kwargs)

        user = User.objects.create_user(**user_data)
        user.set_password(password)
        user.save()

        # Verify user was created correctly
        print(f"\nCreated user: {username}")
        print(f"Is active: {user.is_active}")
        print(f"Is staff: {user.is_staff}")
        print(f"Is superuser: {user.is_superuser}")

        return user, password

    def login(self, username="test_user", password="test_password123"):
        """
        Login helper method.
        Returns True if login successful, False otherwise.
        """
        # Navigate to login page
        self.driver.get(f"{self.live_server_url}/accounts/login/")

        try:
            # Wait for and fill username
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "login")))
            username_input.send_keys(username)

            # Fill password
            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)

            # Find and click the login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            # Wait for successful login by checking for redirect
            self.wait.until(EC.url_changes("/accounts/login/"))

            # Print debug information
            print(f"Current URL after login: {self.driver.current_url}")
            return True

        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def logout(self):
        """Logout helper method."""
        try:
            # Click logout link/button (adjust selector based on your UI)
            logout_link = self.driver.find_element(By.CSS_SELECTOR, "a[href*='logout']")
            logout_link.click()

            # Wait for redirect to login page
            self.wait.until(EC.presence_of_element_located((By.NAME, "username")))
            return True
        except Exception as e:
            print(f"Logout failed: {str(e)}")
            return False

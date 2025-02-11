from selenium.webdriver.common.by import By

from .base import BaseTestCase


class TestAuthentication(BaseTestCase):
    """Test authentication functionality."""

    def setUp(self):
        super().setUp()
        # Create test user with factory
        self.user, self.password = self.create_test_user(
            username="test_user", password="test_password123", is_staff=True
        )

    def test_successful_login(self):
        """Test successful login process."""
        # Attempt login
        login_success = self.login(self.user.username, self.password)
        assert login_success, "Login Failed"

        # Verify successful login by checking welcome message
        assert "Welcome back!" in self.driver.page_source, "Welcome message not found"

    def test_failed_login(self):
        """Test login failure with incorrect credentials."""
        # Attempt login with wrong password
        login_success = self.login(self.user.username, "wrong_password")
        assert not login_success, "Login should fail with incorrect password"

        # Verify we're still on login page
        assert "/accounts/login/" in self.driver.current_url, "Should remain on login page"

        # Verify error message is displayed
        error_message = (self.driver.find_element(By.CLASS_NAME, "alert")).text
        assert "The username and/or password you specified are not correct" in error_message, "Error message not found"

    def test_logout(self):
        """Test logout functionality."""
        # First login
        login_success = self.login(self.user.username, self.password)
        assert login_success, "Initial login failed"

        # Verify we're logged in
        assert "Welcome back!" in self.driver.page_source, "Not properly logged in"

        # Perform logout
        logout_success = self.logout()
        assert logout_success, "Logout failed"

        # Verify redirect to login page
        assert "/accounts/login/" in self.driver.current_url, "Should redirect to login page after logout"

    def tearDown(self):
        """Clean up after each test."""
        super().tearDown()

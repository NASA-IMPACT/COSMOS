from .base import BaseTestCase


class TestAuthentication(BaseTestCase):
    """Test authentication functionality."""

    def setUp(self):
        super().setUp()
        self.test_username = "test_user"
        self.test_password = "test_password123"
        self.user, _ = self.create_test_user(username=self.test_username, password=self.test_password)

    def test_successful_login(self):
        """Test successful login process."""
        # Attempt login
        login_success = self.login(self.test_username, self.test_password)
        assert login_success, "Login should be successful"

        # Verify we're on the dashboard or home page
        assert "Welcome back!" in self.driver.page_source

        # print(self.driver.page_source)

        # # Verify user menu is present
        # user_menu = self.wait.until(
        #     EC.presence_of_element_located((By.CLASS_NAME, "user-menu"))
        # )
        # assert self.test_username in user_menu.text

    # def test_failed_login(self):
    #     """Test login failure with incorrect credentials."""
    #     login_success = self.login(self.test_username, "wrong_password")
    #     assert not login_success, "Login should fail with incorrect password"

    #     # Verify error message
    #     error_message = self.wait.until(
    #         EC.presence_of_element_located((By.CLASS_NAME, "alert-error"))
    #     )
    #     assert "Please enter a correct username and password" in error_message.text

    # def test_logout(self):
    #     """Test logout functionality."""
    #     # First login
    #     login_success = self.login(self.test_username, self.test_password)
    #     assert login_success, "Login should be successful"

    #     # Then logout
    #     logout_success = self.logout()
    #     assert logout_success, "Logout should be successful"

    #     # Verify we're back at login page
    #     assert "login" in self.driver.current_url.lower()

    def tearDown(self):
        """Clean up after each test."""
        self.user.delete()
        super().tearDown()

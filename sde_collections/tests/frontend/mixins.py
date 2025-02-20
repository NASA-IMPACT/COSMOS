from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from ..factories import UserFactory


class AuthenticationMixin:
    """Mixin for authentication-related test methods."""

    def create_test_user(self, username="test_user", password="test_password123", **kwargs):
        """Create a test user using UserFactory."""
        # Delete user if it already exists
        UserFactory._meta.model.objects.filter(username=username).delete()

        user = UserFactory(username=username, is_active=True, **kwargs)
        user.set_password(password)
        user.save()

        return user, password

    def login(self, username="test_user", password="test_password123"):
        """
        Login helper method.
        Returns True if login successful, False otherwise.
        """
        self.driver.get(f"{self.live_server_url}/accounts/login/")

        try:
            username_input = self.wait.until(EC.presence_of_element_located((By.NAME, "login")))
            username_input.send_keys(username)

            password_input = self.driver.find_element(By.NAME, "password")
            password_input.send_keys(password)

            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
            login_button.click()

            self.wait.until(EC.title_is("Collections | COSMOS"))
            return True

        except Exception as e:
            print(f"Login failed: {str(e)}")
            return False

    def logout(self):
        """Logout helper method."""
        try:
            logout_link = self.driver.find_element(By.CSS_SELECTOR, "a[href='/accounts/logout/']")
            self.driver.execute_script("arguments[0].click();", logout_link)

            self.wait.until(EC.presence_of_element_located((By.NAME, "login")))
            return True
        except Exception as e:
            print(f"Logout failed: {str(e)}")
            return False

import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest, HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse

from sde_indexing_helper.users.forms import UserAdminChangeForm
from sde_indexing_helper.users.models import User
from sde_indexing_helper.users.tests.factories import UserFactory
from sde_indexing_helper.users.views import (
    UserRedirectView,
    UserUpdateView,
    user_detail_view,
)

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    Tests for the UserUpdateView.
    """

    @staticmethod
    def dummy_get_response(request: HttpRequest):
        """Dummy get_response method for middleware testing."""
        return None

    def test_get_success_url(self, user: User, rf: RequestFactory):
        """
        Test that UserUpdateView redirects to the correct success URL.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user
        view.request = request

        expected_url = f"/users/{user.username}/"
        assert view.get_success_url() == expected_url, (
            f"Expected {expected_url}, got {view.get_success_url()}"
        )

    def test_get_object(self, user: User, rf: RequestFactory):
        """
        Test that UserUpdateView retrieves the correct user object.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user
        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory):
        """
        Test that form submission in UserUpdateView processes correctly.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add session and message middleware
        SessionMiddleware(self.dummy_get_response).process_request(request)
        MessageMiddleware(self.dummy_get_response).process_request(request)
        request.user = user

        view.request = request

        # Initialize the form
        form = UserAdminChangeForm()
        form.cleaned_data = {}
        form.instance = user
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == ["Information successfully updated"]


class TestUserRedirectView:
    """
    Tests for the UserRedirectView.
    """

    def test_get_redirect_url(self, user: User, rf: RequestFactory):
        """
        Test that UserRedirectView redirects to the "sde_collections:list" URL.
        """
        view = UserRedirectView()
        request = rf.get("/fake-url/")
        request.user = user
        view.request = request

        expected_url = reverse("sde_collections:list")
        assert view.get_redirect_url() == expected_url, (
            f"Expected {expected_url}, got {view.get_redirect_url()}"
        )


class TestUserDetailView:
    """
    Tests for the user_detail_view function.
    """

    def test_authenticated(self, user: User, rf: RequestFactory):
        """
        Test that an authenticated user can access their detail view.
        """
        request = rf.get("/fake-url/")
        request.user = user

        response = user_detail_view(request, username=user.username)

        assert response.status_code == 200

    def test_not_authenticated(self, user: User, rf: RequestFactory):
        """
        Test that an unauthenticated user is redirected to the login page.
        """
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()

        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == 302
        assert response.url == f"{login_url}?next=/fake-url/"

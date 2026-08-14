import pytest
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIClient

from environmental_justice.views import EnvironmentalJusticeRowViewSet

# Create router and register our viewset
router = DefaultRouter()
router.register(r"environmental-justice", EnvironmentalJusticeRowViewSet)

# Create temporary urlpatterns for testing
urlpatterns = [
    path("api/", include(router.urls)),
]


# Override default URL conf for testing
@pytest.fixture
def client():
    """Return a Django REST framework API client"""
    return APIClient()


@pytest.fixture(autouse=True)
def setup_urls(settings):
    """Point ROOT_URLCONF at this module's router-only urlpatterns.

    Uses pytest-django's `settings` fixture so the change is rolled back after each
    test — assigning django.conf.settings directly leaked the EJ-only urlconf into
    every later test module and broke all reverse() calls in a full-suite run."""
    settings.ROOT_URLCONF = __name__

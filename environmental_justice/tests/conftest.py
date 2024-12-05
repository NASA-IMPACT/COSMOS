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
def setup_urls():
    """Setup URLs for testing"""
    from django.conf import settings

    settings.ROOT_URLCONF = __name__

import pytest
from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework.test import APIClient

from sde_collections import views

# Create router and register our viewset
router = DefaultRouter()
router.register(r"delta-urls", views.DeltaURLViewSet)
router.register(r"curated-urls", views.CuratedURLViewSet)
router.register(r"exclude-patterns", views.ExcludePatternViewSet)
router.register(r"include-patterns", views.IncludePatternViewSet)
router.register(r"title-patterns", views.TitlePatternViewSet)
router.register(r"document-type-patterns", views.DocumentTypePatternViewSet)
router.register(r"division-patterns", views.DivisionPatternViewSet)

# Create temporary urlpatterns for testing
urlpatterns = [
    path("api/", include(router.urls)),
    path(
        "delta-urls-api/<str:config_folder>/",
        view=views.DeltaURLAPIView.as_view(),
        name="delta-url-api",
    ),
    path("curated-urls-api/<str:config_folder>/", view=views.CuratedURLAPIView.as_view(), name="curated-url-api"),
    path(
        "candidate-urls-api/<str:config_folder>/",
        view=views.CuratedURLAPIView.as_view(),
        name="candidate-url-api",
    ),
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

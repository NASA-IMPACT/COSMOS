from django.urls import include, path
from rest_framework import routers

from .views import (
    CandidateURLBulkCreateView,
    CandidateURLsListView,
    CandidateURLViewSet,
    CollectionDetailView,
    CollectionListView,
    CollectionViewSet,
    DocumentTypePatternViewSet,
    ExcludePatternViewSet,
    RequiredUrlsDeleteView,
    TitlePatternViewSet,
)

router = routers.DefaultRouter()
router.register(r"collections", CollectionViewSet)
router.register(r"candidate-urls", CandidateURLViewSet)
router.register(r"exclude-patterns", ExcludePatternViewSet)
router.register(r"title-patterns", TitlePatternViewSet)
router.register(r"document-type-patterns", DocumentTypePatternViewSet)

app_name = "sde_collections"

urlpatterns = [
    path("", view=CollectionListView.as_view(), name="list"),
    path("<int:pk>/", view=CollectionDetailView.as_view(), name="detail"),
    path(
        "api/candidate-urls/<str:config_folder>/bulk-create/",
        CandidateURLBulkCreateView.as_view(),
        name="candidate-urls-bulk-create",
    ),
    path(
        "delete-required-url/<int:pk>",
        view=RequiredUrlsDeleteView.as_view(),
        name="delete_required_url",
    ),
    path(
        "<int:pk>/candidate-urls",
        view=CandidateURLsListView.as_view(),
        name="candidate_urls",
    ),
    # List all CandidateURL instances: /candidate-urls/
    # Retrieve a specific CandidateURL instance: /candidate-urls/{id}/
    # Create a new CandidateURL instance: /candidate-urls/
    # Update an existing CandidateURL instance: /candidate-urls/{id}/
    # Delete an existing CandidateURL instance: /candidate-urls/{id}/
    path("api/", include(router.urls)),
]

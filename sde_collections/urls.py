from django.urls import include, path
from rest_framework import routers

from . import views

router = routers.DefaultRouter()
router.register(r"collections", views.CollectionViewSet)
router.register(r"collections-read", views.CollectionReadViewSet)
router.register(r"candidate-urls", views.CandidateURLViewSet)
router.register(r"exclude-patterns", views.ExcludePatternViewSet)
router.register(r"include-patterns", views.IncludePatternViewSet)
router.register(r"title-patterns", views.TitlePatternViewSet)
router.register(r"document-type-patterns", views.DocumentTypePatternViewSet)

app_name = "sde_collections"

urlpatterns = [
    path("", view=views.CollectionListView.as_view(), name="list"),
    path("<int:pk>/", view=views.CollectionDetailView.as_view(), name="detail"),
    path(
        "api/collections/push_to_github/",
        views.PushToGithubView.as_view(),
        name="push-to-github",
    ),
    path(
        "delete-required-url/<int:pk>",
        view=views.RequiredUrlsDeleteView.as_view(),
        name="delete_required_url",
    ),
    path(
        "<int:pk>/candidate-urls",
        view=views.CandidateURLsListView.as_view(),
        name="candidate_urls",
    ),
    path(
        "consolidate/",
        view=views.WebappGitHubConsolidationView.as_view(),
        name="consolidate_db_and_github_configs",
    ),
    # List all CandidateURL instances: /candidate-urls/
    # Retrieve a specific CandidateURL instance: /candidate-urls/{id}/
    # Create a new CandidateURL instance: /candidate-urls/
    # Update an existing CandidateURL instance: /candidate-urls/{id}/
    # Delete an existing CandidateURL instance: /candidate-urls/{id}/
    path("api/", include(router.urls)),
]

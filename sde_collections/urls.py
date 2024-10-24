from django.urls import include, path
from rest_framework import routers

from environmental_justice.views import EnvironmentalJusticeRowViewSet

from . import views

router = routers.DefaultRouter()
router.register(r"collections", views.CollectionViewSet, basename="collection")
router.register(r"collections-read", views.CollectionReadViewSet, basename="collection-read")
router.register(r"candidate-urls", views.CandidateURLViewSet)
router.register(r"exclude-patterns", views.ExcludePatternViewSet)
router.register(r"include-patterns", views.IncludePatternViewSet)
router.register(r"title-patterns", views.TitlePatternViewSet)
router.register(r"document-type-patterns", views.DocumentTypePatternViewSet)
router.register(r"division-patterns", views.DivisionPatternViewSet)
router.register(r"environmental-justice", EnvironmentalJusticeRowViewSet)

app_name = "sde_collections"

urlpatterns = [
    path("", view=views.CollectionListView.as_view(), name="list"),
    path("sde-dashboard/", view=views.SdeDashboardView.as_view(), name="dashboard"),
    path("<int:pk>/", view=views.CollectionDetailView.as_view(), name="detail"),
    path(
        "api/collections/push_to_github/",
        views.PushToGithubView.as_view(),
        name="push-to-github",
    ),
    path(
        "api/indexing_instructions/",
        views.IndexingInstructionsView.as_view(),
        name="indexing_instructions",
    ),
    path("api/assign-division/<int:pk>/", views.CandidateURLViewSet.as_view({"post": "update_division"})),
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
    path(
        "candidate-urls-api/<str:config_folder>/",
        view=views.CandidateURLAPIView.as_view(),
        name="candidate-url-api",
    ),
    path("titles-and-errors/", views.TitlesAndErrorsView.as_view(), name="titles-and-errors-list"),
]

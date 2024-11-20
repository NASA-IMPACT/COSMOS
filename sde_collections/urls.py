from django.urls import include, path
from rest_framework import routers

from environmental_justice.views import EnvironmentalJusticeRowViewSet

from . import views

router = routers.DefaultRouter()
router.register(r"collections", views.CollectionViewSet, basename="collection")
router.register(r"collections-read", views.CollectionReadViewSet, basename="collection-read")
router.register(r"delta-urls", views.DeltaURLViewSet)
router.register(r"curated-urls", views.CuratedURLViewSet)
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
    path("api/assign-division/<int:pk>/", views.DeltaURLViewSet.as_view({"post": "update_division"})),
    path(
        "delete-required-url/<int:pk>",
        view=views.RequiredUrlsDeleteView.as_view(),
        name="delete_required_url",
    ),
    path(
        "<int:pk>/delta-urls",
        view=views.DeltaURLsListView.as_view(),
        name="delta_urls",
    ),
    path(
        "consolidate/",
        view=views.WebappGitHubConsolidationView.as_view(),
        name="consolidate_db_and_github_configs",
    ),
    # List all DeltaURL instances: /delta-urls/
    # Retrieve a specific DeltaURL instance: /delta-urls/{id}/
    # Create a new DeltaURL instance: /delta-urls/
    # Update an existing DeltaURL instance: /delta-urls/{id}/
    # Delete an existing DeltaURL instance: /delta-urls/{id}/
    path("api/", include(router.urls)),
    path(
        "delta-urls-api/<str:config_folder>/",
        view=views.DeltaURLAPIView.as_view(),
        name="delta-url-api",
    ),
    path("curated-urls-api/<str:config_folder>/", view=views.CuratedURLAPIView.as_view(), name="curated-url-api"),
    path(
        "candidate-url-api/<str:config_folder>/",
        view=views.CuratedURLAPIView.as_view(),
        name="candidate-url-api",
    ),
    path("titles-and-errors/", views.TitlesAndErrorsView.as_view(), name="titles-and-errors-list"),
]

from django.urls import path

from sde_collections.views import (
    CandidateURLsListView,
    CollectionDetailView,
    CollectionListView,
)

app_name = "sde_collections"
urlpatterns = [
    path("", view=CollectionListView.as_view(), name="list"),
    path("<int:pk>/", view=CollectionDetailView.as_view(), name="detail"),
    path(
        "<int:pk>/candidate-urls",
        view=CandidateURLsListView.as_view(),
        name="candidate_urls",
    ),
]

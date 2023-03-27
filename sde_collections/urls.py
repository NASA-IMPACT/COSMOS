from django.urls import path

from sde_collections.views import CollectionListView

app_name = "sde_collections"
urlpatterns = [
    path("", view=CollectionListView.as_view(), name="list"),
]

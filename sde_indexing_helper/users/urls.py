from django.urls import path

from sde_indexing_helper.users.views import (
    ContactFormModelView,
    ContentCurationRequestView,
    user_detail_view,
    user_redirect_view,
    user_update_view,
)

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
    path("api/contact-us/", ContactFormModelView.as_view(), name="contact-us-api"),
    path(
        "api/content-curation-request/",
        ContentCurationRequestView.as_view(),
        name="content-curation-request-api",
    ),
]

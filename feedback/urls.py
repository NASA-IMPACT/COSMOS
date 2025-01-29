from django.urls import path

from .views import (
    ContactFormModelView,
    ContentCurationRequestView,
    FeedbackFormDropdownListView,
)

app_name = "feedback"
urlpatterns = [
    path("contact-us-api/", ContactFormModelView.as_view(), name="contact-us-api"),
    path(
        "feedback-form-dropdown-options-api/",
        FeedbackFormDropdownListView.as_view(),
        name="feedback-form-dropdown-options-api",
    ),
    path(
        "content-curation-request-api/",
        ContentCurationRequestView.as_view(),
        name="content-curation-request-api",
    ),
]

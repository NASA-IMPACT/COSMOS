from django.urls import path

from .views import ContactFormModelView, ContentCurationRequestView

app_name = "feedback"
urlpatterns = [
    path("contact-us-api/", ContactFormModelView.as_view(), name="contact-us-api"),
    path(
        "content-curation-request-api/",
        ContentCurationRequestView.as_view(),
        name="content-curation-request-api",
    ),
]

from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import ContactFormModelView, ContentCurationRequestView

app_name = "feedback"
urlpatterns = [
    path("contact-us-api/", ContactFormModelView.as_view(), name="contact-us-api"),
    path(
        "content-curation-request-api/",
        ContentCurationRequestView.as_view(),
        name="content-curation-request-api",
    ),
    path(
        "contact-us-api/token/", TokenObtainPairView.as_view(), name="token-obtain-pair"
    ),
    path(
        "content-curation-request-api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token-refresh",
    ),
]

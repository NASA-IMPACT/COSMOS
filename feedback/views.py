from rest_framework import generics

from .models import ContentCurationRequest, Feedback, FeedbackFormDropdown
from .serializers import (
    ContentCurationRequestSerializer,
    FeedbackFormDropdownSerializer,
    FeedbackSerializer,
)


class ContactFormModelView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer


class FeedbackFormDropdownListView(generics.ListAPIView):
    queryset = FeedbackFormDropdown.objects.all()
    serializer_class = FeedbackFormDropdownSerializer


class ContentCurationRequestView(generics.CreateAPIView):
    queryset = ContentCurationRequest.objects.all()
    serializer_class = ContentCurationRequestSerializer

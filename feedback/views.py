from rest_framework import generics

from .models import ContentCurationRequest, Feedback
from .serializers import ContentCurationRequestSerializer, FeedbackSerializer


class ContactFormModelView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer


class ContentCurationRequestView(generics.CreateAPIView):
    queryset = ContentCurationRequest.objects.all()
    serializer_class = ContentCurationRequestSerializer

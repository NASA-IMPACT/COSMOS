from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import ContentCurationRequest, Feedback
from .serializers import ContentCurationRequestSerializer, FeedbackSerializer


class ContactFormModelView(generics.CreateAPIView):
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [IsAuthenticated]


class ContentCurationRequestView(generics.CreateAPIView):
    queryset = ContentCurationRequest.objects.all()
    serializer_class = ContentCurationRequestSerializer
    permission_classes = [IsAuthenticated]

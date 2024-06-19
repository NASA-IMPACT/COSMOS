from rest_framework import serializers

from .models import ContentCurationRequest, Feedback


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = [
            "name",
            "email",
            "subject",
            "comments",
            "source",
            "created_at",
        ]


class ContentCurationRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCurationRequest
        fields = [
            "name",
            "email",
            "scientific_focus",
            "data_type",
            "data_link",
            "additional_info",
            "created_at",
        ]

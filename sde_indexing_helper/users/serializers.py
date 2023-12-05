from rest_framework import serializers

from .models import ContactFormModel, ContentCurationRequestModel


class ContactFormModelSerializer(serializers.ModelSerializer):
    Name = serializers.CharField(write_only=True, source="name")
    Email = serializers.EmailField(write_only=True, source="email")
    Subject = serializers.CharField(write_only=True, source="subject")
    comments_questions = serializers.CharField(write_only=True, source="comment")

    class Meta:
        model = ContactFormModel
        fields = ["Name", "Email", "Subject", "comments_questions"]


class ContentCurationRequestModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentCurationRequestModel
        fields = [
            "name",
            "email",
            "scientific_focus",
            "data_type",
            "data_link",
            "additional_info",
        ]

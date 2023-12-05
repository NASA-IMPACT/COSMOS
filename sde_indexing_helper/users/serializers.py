from rest_framework import serializers

from .models import ContactFormModel


class ContactFormModelSerializer(serializers.ModelSerializer):
    Name = serializers.CharField(write_only=True, source="name")
    Email = serializers.EmailField(write_only=True, source="email")
    Subject = serializers.CharField(write_only=True, source="subject")
    comments_questions = serializers.CharField(write_only=True, source="comment")

    class Meta:
        model = ContactFormModel
        fields = ["Name", "Email", "Subject", "comments_questions"]

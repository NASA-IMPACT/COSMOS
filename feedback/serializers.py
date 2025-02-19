import re

from rest_framework import serializers

from .models import ContentCurationRequest, Feedback, FeedbackFormDropdown


class FeedbackFormDropdownSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackFormDropdown
        fields = ["id", "name"]


class HTMLFreeCharField(serializers.CharField):
    def to_internal_value(self, data):
        value = super().to_internal_value(data)

        if re.search(r"<[^>]+>", value):
            raise serializers.ValidationError("HTML tags are not allowed in this field")

        return value


class FeedbackSerializer(serializers.ModelSerializer):

    name = HTMLFreeCharField()
    subject = HTMLFreeCharField()
    comments = HTMLFreeCharField()
    source = HTMLFreeCharField()

    class Meta:
        model = Feedback
        fields = [
            "name",
            "email",
            "subject",
            "comments",
            "source",
            "dropdown_option",
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

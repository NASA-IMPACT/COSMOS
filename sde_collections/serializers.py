from rest_framework import serializers

from .models import CandidateURL, ExcludePattern, TitlePattern


class CandidateURLSerializer(serializers.ModelSerializer):
    excluded = serializers.BooleanField(required=False)
    url = serializers.CharField(required=False)

    class Meta:
        model = CandidateURL
        fields = (
            "id",
            "excluded",
            "url",
            "scraped_title",
            "generated_title",
            "visited",
        )


class ExcludePatternSerializer(serializers.ModelSerializer):
    pattern_type_display = serializers.CharField(
        source="get_pattern_type_display", read_only=True
    )

    class Meta:
        model = ExcludePattern
        fields = (
            "id",
            "collection",
            "match_pattern",
            "pattern_type",
            "reason",
            "pattern_type_display",
        )


class TitlePatternSerializer(serializers.ModelSerializer):
    pattern_type_display = serializers.CharField(
        source="get_pattern_type_display", read_only=True
    )

    class Meta:
        model = TitlePattern
        fields = (
            "id",
            "collection",
            "match_pattern",
            "pattern_type",
            "title_pattern",
            "pattern_type_display",
        )

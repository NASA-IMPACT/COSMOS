from rest_framework import serializers

from .models import CandidateURL, ExcludePattern, TitlePattern


class CandidateURLSerializer(serializers.ModelSerializer):
    is_excluded = serializers.SerializerMethodField()

    def get_is_excluded(self, obj):
        return obj.excludepattern_set.exists()

    class Meta:
        model = CandidateURL
        fields = (
            "id",
            "scraped_title",
            "generated_title",
            "level",
            "is_excluded",
            "visited",
        )


class ExcludePatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExcludePattern
        fields = ("id", "collection", "match_pattern", "reason")


class TitlePatternSerializer(serializers.ModelSerializer):
    class Meta:
        model = TitlePattern
        fields = ("id", "collection", "match_pattern", "title_pattern")

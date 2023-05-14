import re

import lxml.etree
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

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
    candidate_urls_count = serializers.SerializerMethodField(read_only=True)

    def get_candidate_urls_count(self, instance):
        return instance.candidate_urls.count()

    class Meta:
        model = ExcludePattern
        fields = (
            "id",
            "collection",
            "match_pattern",
            "pattern_type",
            "reason",
            "pattern_type_display",
            "candidate_urls_count",
        )


class TitlePatternSerializer(serializers.ModelSerializer):
    match_pattern_type_display = serializers.CharField(
        source="get_match_pattern_type_display", read_only=True
    )
    title_pattern_type_display = serializers.CharField(
        source="get_title_pattern_type_display", read_only=True
    )

    class Meta:
        model = TitlePattern
        fields = (
            "id",
            "collection",
            "match_pattern",
            "match_pattern_type",
            "match_pattern_type_display",
            "title_pattern",
            "title_pattern_type",
            "title_pattern_type_display",
        )

    def validate(self, value):
        if value["title_pattern_type"] == 2:  # modifier
            if not all(
                var == "title"
                for var in re.findall(r"\{(.*?)\}", value["title_pattern"])
            ):
                # ensure valid modifier
                raise ValidationError(
                    "Variable is used but is not valid. Please only use {title}."
                )
        elif value["title_pattern_type"] == 3:  # xpath
            # ensure valid xpath
            print(value["title_pattern"])
            try:
                lxml.etree.XPath(rf'{value["title_pattern"]}')
            except lxml.etree.XPathSyntaxError:
                raise ValidationError("Invalid xpath")

        return value

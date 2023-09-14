from rest_framework import serializers

from .models.candidate_url import CandidateURL
from .models.collection import Collection
from .models.collection_choice_fields import DocumentTypes
from .models.pattern import DocumentTypePattern, ExcludePattern, TitlePattern


class CollectionSerializer(serializers.ModelSerializer):
    curation_status_display = serializers.CharField(
        source="get_curation_status_display", read_only=True
    )

    class Meta:
        model = Collection
        fields = (
            "id",
            "curation_status",
            "curation_status_display",
            "curated_by",
        )
        # extra_kwargs = {
        #     "name": {"required": False},
        #     "config_folder": {"required": False},
        #     "division": {"required": False},
        # }


class CandidateURLSerializer(serializers.ModelSerializer):
    excluded = serializers.BooleanField(required=False)
    document_type_display = serializers.CharField(
        source="get_document_type_display", read_only=True
    )
    url = serializers.CharField(required=False)
    generated_title_id = serializers.SerializerMethodField(read_only=True)
    match_pattern_type = serializers.SerializerMethodField(read_only=True)
    candidate_urls_count = serializers.SerializerMethodField(read_only=True)
    inference_by = serializers.CharField(read_only=True)

    def get_candidate_urls_count(self, obj):
        titlepattern = obj.titlepattern_urls.last()
        return titlepattern.candidate_urls.count() if titlepattern else 0

    def get_generated_title_id(self, obj):
        titlepattern = obj.titlepattern_urls.last()
        return titlepattern.id if titlepattern else None

    def get_match_pattern_type(self, obj):
        titlepattern = obj.titlepattern_urls.last()
        return titlepattern.match_pattern_type if titlepattern else None

    class Meta:
        model = CandidateURL
        fields = (
            "id",
            "excluded",
            "url",
            "scraped_title",
            "generated_title",
            "generated_title_id",
            "match_pattern_type",
            "candidate_urls_count",
            "document_type",
            "document_type_display",
            "visited",
            "inference_by",
        )


class CandidateURLBulkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CandidateURL
        fields = (
            "url",
            "scraped_title",
        )


class BasePatternSerializer(serializers.ModelSerializer):
    match_pattern_type_display = serializers.CharField(
        source="get_match_pattern_type_display", read_only=True
    )
    candidate_urls_count = serializers.SerializerMethodField(read_only=True)

    def get_candidate_urls_count(self, instance):
        return instance.candidate_urls.count()

    class Meta:
        fields = (
            "id",
            "collection",
            "match_pattern",
            "match_pattern_type",
            "match_pattern_type_display",
            "candidate_urls_count",
        )
        abstract = True


class ExcludePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    class Meta:
        model = ExcludePattern
        fields = BasePatternSerializer.Meta.fields + ("reason",)


class TitlePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    class Meta:
        model = TitlePattern
        fields = BasePatternSerializer.Meta.fields + ("title_pattern",)

    def validate_match_pattern(self, value):
        try:
            title_pattern = TitlePattern.objects.get(
                match_pattern=value,
                match_pattern_type=TitlePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            )
            title_pattern.delete()
        except TitlePattern.DoesNotExist:
            pass
        return value


class DocumentTypePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    document_type_display = serializers.CharField(
        source="get_document_type_display", read_only=True
    )
    document_type = serializers.ChoiceField(
        choices=DocumentTypes.choices
        + [
            (0, "None"),
        ]
    )

    class Meta:
        model = DocumentTypePattern
        fields = BasePatternSerializer.Meta.fields + (
            "document_type",
            "document_type_display",
        )

    def validate_match_pattern(self, value):
        try:
            title_pattern = DocumentTypePattern.objects.get(
                match_pattern=value,
                match_pattern_type=DocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            )
            title_pattern.delete()
        except DocumentTypePattern.DoesNotExist:
            pass
        return value

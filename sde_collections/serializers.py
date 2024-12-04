from rest_framework import serializers

from .models.collection import Collection, WorkflowHistory
from .models.collection_choice_fields import Divisions, DocumentTypes
from .models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaDocumentTypePattern,
    DeltaExcludePattern,
    DeltaIncludePattern,
    DeltaTitlePattern,
)
from .models.delta_url import CuratedUrl, DeltaUrl


class CollectionSerializer(serializers.ModelSerializer):
    curation_status_display = serializers.CharField(source="get_curation_status_display", read_only=True)
    workflow_status_display = serializers.CharField(source="get_workflow_status_display", read_only=True)

    class Meta:
        model = Collection
        fields = (
            "id",
            "curation_status",
            "workflow_status",
            "curation_status_display",
            "workflow_status_display",
            "curated_by",
            "division",
            "document_type",
            "name",
        )
        extra_kwargs = {
            "division": {"required": False},
            "document_type": {"required": False},
            "name": {"required": False},
        }

        # extra_kwargs = {
        #     "name": {"required": False},
        #     "config_folder": {"required": False},
        #     "division": {"required": False},
        # }


class CollectionReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Collection
        fields = "__all__"


class WorkflowHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkflowHistory
        fields = "__all__"


class DeltaURLSerializer(serializers.ModelSerializer):
    excluded = serializers.BooleanField(required=False)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    division_display = serializers.CharField(source="get_division_display", read_only=True)
    url = serializers.CharField(required=False)
    generated_title_id = serializers.SerializerMethodField(read_only=True)
    match_pattern_type = serializers.SerializerMethodField(read_only=True)
    delta_urls_count = serializers.SerializerMethodField(read_only=True)

    def get_delta_urls_count(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.delta_urls.count() if titlepattern else 0

    def get_generated_title_id(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.id if titlepattern else None

    def get_match_pattern_type(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.match_pattern_type if titlepattern else None

    class Meta:
        model = DeltaUrl
        fields = (
            "id",
            "excluded",
            "url",
            "scraped_title",
            "generated_title",
            "generated_title_id",
            "match_pattern_type",
            "delta_urls_count",
            "document_type",
            "document_type_display",
            "division",
            "division_display",
            "visited",
        )


class CuratedURLSerializer(serializers.ModelSerializer):
    excluded = serializers.BooleanField(required=False)
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    division_display = serializers.CharField(source="get_division_display", read_only=True)
    url = serializers.CharField(required=False)
    generated_title_id = serializers.SerializerMethodField(read_only=True)
    match_pattern_type = serializers.SerializerMethodField(read_only=True)
    curated_urls_count = serializers.SerializerMethodField(read_only=True)

    def get_curated_urls_count(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.curated_urls.count() if titlepattern else 0

    def get_generated_title_id(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.id if titlepattern else None

    def get_match_pattern_type(self, obj):
        titlepattern = obj.deltatitlepatterns.last()
        return titlepattern.match_pattern_type if titlepattern else None

    class Meta:
        model = CuratedUrl
        fields = (
            "id",
            "excluded",
            "url",
            "scraped_title",
            "generated_title",
            "generated_title_id",
            "match_pattern_type",
            "curated_urls_count",
            "document_type",
            "document_type_display",
            "division",
            "division_display",
            "visited",
        )


class DeltaURLBulkCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeltaUrl
        fields = (
            "url",
            "scraped_title",
        )


class DeltaURLAPISerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    tree_root = serializers.SerializerMethodField()

    class Meta:
        model = DeltaUrl
        fields = (
            "url",
            "title",
            "document_type",
            "file_extension",
            "tree_root",
        )

    def get_document_type(self, obj):
        if obj.document_type is not None:
            return obj.get_document_type_display()
        elif obj.collection.document_type is not None:
            return obj.collection.get_document_type_display()
        else:
            return "Unknown"

    def get_title(self, obj):
        return obj.generated_title if obj.generated_title else obj.scraped_title

    def get_file_extension(self, obj):
        return obj.fileext

    def get_tree_root(self, obj):
        if obj.collection.is_multi_division:
            if obj.division:
                return f"/{obj.get_division_display()}/{obj.collection.name}/"
            else:
                return f"/{obj.collection.get_division_display()}/{obj.collection.name}/"
        else:
            return obj.collection.tree_root


class CuratedURLAPISerializer(serializers.ModelSerializer):
    document_type = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    tree_root = serializers.SerializerMethodField()

    class Meta:
        model = CuratedUrl
        fields = (
            "url",
            "title",
            "document_type",
            "file_extension",
            "tree_root",
        )

    def get_document_type(self, obj):
        if obj.document_type is not None:
            return obj.get_document_type_display()
        elif obj.collection.document_type is not None:
            return obj.collection.get_document_type_display()
        else:
            return "Unknown"

    def get_title(self, obj):
        return obj.generated_title if obj.generated_title else obj.scraped_title

    def get_file_extension(self, obj):
        return obj.fileext

    def get_tree_root(self, obj):
        if obj.collection.is_multi_division:
            if obj.division:
                return f"/{obj.get_division_display()}/{obj.collection.name}/"
            else:
                return f"/{obj.collection.get_division_display()}/{obj.collection.name}/"
        else:
            return obj.collection.tree_root


class BasePatternSerializer(serializers.ModelSerializer):
    match_pattern_type_display = serializers.CharField(source="get_match_pattern_type_display", read_only=True)
    delta_urls_count = serializers.SerializerMethodField(read_only=True)

    def get_delta_urls_count(self, instance):
        return instance.delta_urls.count()

    class Meta:
        fields = (
            "id",
            "collection",
            "match_pattern",
            "match_pattern_type",
            "match_pattern_type_display",
            "delta_urls_count",
        )
        abstract = True


class ExcludePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    class Meta:
        model = DeltaExcludePattern
        fields = BasePatternSerializer.Meta.fields + ("reason",)


class IncludePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    class Meta:
        model = DeltaIncludePattern
        fields = BasePatternSerializer.Meta.fields


class TitlePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    class Meta:
        model = DeltaTitlePattern
        fields = BasePatternSerializer.Meta.fields + ("title_pattern",)

    def validate_match_pattern(self, value):
        try:
            title_pattern = DeltaTitlePattern.objects.get(
                match_pattern=value,
                match_pattern_type=DeltaTitlePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            )
            title_pattern.delete()
        except DeltaTitlePattern.DoesNotExist:
            pass
        return value


class DocumentTypePatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    document_type_display = serializers.CharField(source="get_document_type_display", read_only=True)
    document_type = serializers.ChoiceField(
        choices=DocumentTypes.choices
        + [
            (0, "None"),
        ]
    )

    class Meta:
        model = DeltaDocumentTypePattern
        fields = BasePatternSerializer.Meta.fields + (
            "document_type",
            "document_type_display",
        )

    def validate_match_pattern(self, value):
        try:
            title_pattern = DeltaDocumentTypePattern.objects.get(
                match_pattern=value,
                match_pattern_type=DeltaDocumentTypePattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            )
            title_pattern.delete()
        except DeltaDocumentTypePattern.DoesNotExist:
            pass
        return value


class DivisionPatternSerializer(BasePatternSerializer, serializers.ModelSerializer):
    division_display = serializers.CharField(source="get_division_display", read_only=True)
    division = serializers.ChoiceField(choices=Divisions.choices)

    class Meta:
        model = DeltaDivisionPattern
        fields = BasePatternSerializer.Meta.fields + (
            "division",
            "division_display",
        )

    def validate_match_pattern(self, value):
        try:
            division_pattern = DeltaDivisionPattern.objects.get(
                match_pattern=value,
                match_pattern_type=DeltaDivisionPattern.MatchPatternTypeChoices.INDIVIDUAL_URL,
            )
            division_pattern.delete()
        except DeltaDivisionPattern.DoesNotExist:
            pass
        return value

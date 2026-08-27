import csv

from django import forms
from django.contrib import admin, messages
from django.http import HttpResponse

from sde_collections.models.delta_patterns import (
    DeltaDivisionPattern,
    DeltaResolvedTitle,
    DeltaTitlePattern,
)

from .models.candidate_url import CandidateURL, ResolvedTitle
from .models.collection import Collection, ReindexingHistory, WorkflowHistory
from .models.collection_choice_fields import TDAMMTags
from .models.delta_url import CuratedUrl, DeltaUrl, DumpUrl
from .models.indexing import IndexDispatch
from .models.pattern import DivisionPattern, IncludePattern, TitlePattern
from .models.scraper_config import ScrapeDispatch, ScraperConfigOverride


@admin.action(description="Download candidate URLs as csv")
def download_candidate_urls_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="candidate_urls.csv"'

    writer = csv.writer(response)

    if len(queryset) > 1:
        messages.add_message(request, messages.ERROR, "You can only export one collection at a time.")
        return

    urls = CandidateURL.objects.filter(collection=queryset.first()).values_list("url", flat=True)

    # Write your headers here
    writer.writerow(["candidate_url"])
    for url in urls:
        writer.writerow([url])

    return response


@admin.action(description="Generate candidate URLs")
def generate_candidate_urls(modeladmin, request, queryset):
    collection = queryset.first()
    collection.generate_candidate_urls()
    messages.add_message(
        request,
        messages.INFO,
        f"Started generating candidate URLs for: {collection.name}",
    )


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"  # noqa: E702
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export selected as csv"


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin, ExportCsvMixin):
    """Admin View for Collection"""

    fieldsets = (
        (
            "Essential information",
            {
                "fields": (
                    "name",
                    "config_folder",
                    "url",
                    "division",
                    "document_type",
                    "update_frequency",
                    "source",
                    "turned_on",
                    "is_multi_division",
                    "reindexing_status",
                ),
            },
        ),
        (
            "Advanced options",
            {
                "classes": ("collapse",),
                "fields": (
                    "delete",
                    "audit_hierarchy",
                    "audit_url",
                    "audit_mapping",
                    "audit_label",
                    "audit_query",
                    "audit_duplicate_results",
                    "audit_metrics",
                    "cleaning_assigned_to",
                    "notes",
                ),
            },
        ),
    )

    list_display = (
        "name",
        "candidate_urls_count",
        "included_candidate_urls_count",
        "delta_urls_count",
        "included_delta_urls_count",
        "included_curated_urls_count",
        "config_folder",
        "url",
        "division",
        "new_collection",
        "is_multi_division",
        "reindexing_status",
    )

    def included_candidate_urls_count(self, obj) -> int:
        return obj.candidate_urls.filter(excluded=False).count()

    included_candidate_urls_count.short_description = "Included Candidate URLs Count"

    def delta_urls_count(self, obj) -> int:
        return obj.delta_urls.count()

    delta_urls_count.short_description = "Total Delta URLs Count"

    def included_delta_urls_count(self, obj) -> int:
        return obj.delta_urls.filter(excluded=False).count()

    included_delta_urls_count.short_description = "Included Delta URLs Count"

    def included_curated_urls_count(self, obj) -> int:
        return obj.curated_urls.filter(excluded=False).count()

    included_curated_urls_count.short_description = "Included Curated URLs Count"

    readonly_fields = ("config_folder",)
    list_filter = (
        "division",
        "curation_status",
        "workflow_status",
        "turned_on",
        "is_multi_division",
        "reindexing_status",
    )
    search_fields = ("name", "url", "config_folder")
    actions = [
        "export_as_csv",
        download_candidate_urls_as_csv,
    ]
    ordering = ("cleaning_order",)


@admin.action(description="Exclude URL and all children")
def exclude_pattern(modeladmin, request, queryset):
    for candidate_url in queryset.all():
        candidate_url.set_excluded(True)


@admin.action(description="Include URL and all children")
def include_pattern(modeladmin, request, queryset):
    for candidate_url in queryset.all():
        candidate_url.set_excluded(False)


@admin.action(description="Exclude pattern and delete children")
def exclude_and_delete_children(modeladmin, request, queryset):
    queryset.update(excluded=True)
    for candidate_url in queryset.all():
        candidate_url.get_children().delete()


class TDAMMFormMixin(forms.ModelForm):
    """Mixin for forms that need TDAMM tag fields"""

    tdamm_tag_manual = forms.MultipleChoiceField(
        choices=TDAMMTags.choices,
        required=False,
        label="TDAMM Manual Tags",
        widget=forms.CheckboxSelectMultiple,
    )

    tdamm_tag_ml = forms.MultipleChoiceField(
        choices=TDAMMTags.choices,
        required=False,
        label="TDAMM ML Tags",
        widget=forms.CheckboxSelectMultiple,
    )


class TDAMMAdminMixin:
    """Mixin for admin classes that handle TDAMM tags"""

    list_display = ("url", "scraped_title", "generated_title", "collection")
    list_filter = ["collection"]
    search_fields = ("url", "collection__name")

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (
                "Overall Information",
                {
                    "fields": (
                        "collection",
                        "url",
                        "scraped_title",
                        "scraped_text",
                        "generated_title",
                        "visited",
                        "document_type",
                        "division",
                    )
                },
            ),
            (
                "TDAMM Tags",
                {
                    "fields": (
                        "tdamm_tag_ml",
                        "tdamm_tag_manual",
                    ),
                    "classes": ("collapse",),
                },
            ),
        ]
        return fieldsets


class CandidateURLForm(TDAMMFormMixin):
    class Meta:
        model = CandidateURL
        fields = "__all__"


class DumpURLForm(TDAMMFormMixin, forms.ModelForm):
    class Meta:
        model = DumpUrl
        fields = "__all__"


class DeltaURLForm(TDAMMFormMixin, forms.ModelForm):
    class Meta:
        model = DeltaUrl
        fields = "__all__"


class CuratedURLForm(TDAMMFormMixin, forms.ModelForm):
    class Meta:
        model = CuratedUrl
        fields = "__all__"


class CandidateURLAdmin(TDAMMAdminMixin, admin.ModelAdmin):
    """Admin view for CandidateURL"""

    form = CandidateURLForm


class TitlePatternAdmin(admin.ModelAdmin):
    """Admin View for TitlePattern"""

    list_display = (
        "match_pattern",
        "title_pattern",
        "collection",
        "match_pattern_type",
    )
    list_filter = (
        "match_pattern_type",
        "collection",
    )


class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ("collection", "old_status", "workflow_status", "created_at")
    search_fields = ["collection__name"]
    list_filter = ["workflow_status", "old_status"]


class ReindexingHistoryAdmin(admin.ModelAdmin):
    list_display = ("collection", "old_status", "reindexing_status", "created_at")
    search_fields = ["collection__name"]
    list_filter = ["reindexing_status", "old_status"]


class ResolvedTitleAdmin(admin.ModelAdmin):
    list_display = ["title_pattern", "candidate_url", "resolved_title", "created_at"]


class DivisionPatternAdmin(admin.ModelAdmin):
    list_display = ("collection", "match_pattern", "division")
    search_fields = ("match_pattern", "division")


# deltas below
class DeltaTitlePatternAdmin(admin.ModelAdmin):
    """Admin View for DeltaTitlePattern"""

    list_display = (
        "match_pattern",
        "title_pattern",
        "collection",
        "match_pattern_type",
    )
    list_filter = (
        "match_pattern_type",
        "collection",
    )


class DeltaResolvedTitleAdmin(admin.ModelAdmin):
    list_display = ["title_pattern", "delta_url", "resolved_title", "created_at"]


class DeltaDivisionPatternAdmin(admin.ModelAdmin):
    list_display = ("collection", "match_pattern", "division")
    search_fields = ("match_pattern", "division")


class DumpUrlAdmin(TDAMMAdminMixin, admin.ModelAdmin):
    """Admin View for DumpUrl"""

    form = DumpURLForm


class DeltaUrlAdmin(TDAMMAdminMixin, admin.ModelAdmin):
    """Admin View for DeltaUrl"""

    form = DeltaURLForm

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        fieldsets[0][1]["fields"] += ("to_delete",)
        return fieldsets


class CuratedUrlAdmin(TDAMMAdminMixin, admin.ModelAdmin):
    """Admin View for CuratedUrl"""

    form = CuratedURLForm


admin.site.register(ReindexingHistory, ReindexingHistoryAdmin)
admin.site.register(WorkflowHistory, WorkflowHistoryAdmin)
admin.site.register(CandidateURL, CandidateURLAdmin)
admin.site.register(TitlePattern, TitlePatternAdmin)
admin.site.register(IncludePattern)
admin.site.register(ResolvedTitle, ResolvedTitleAdmin)
admin.site.register(DivisionPattern, DivisionPatternAdmin)


admin.site.register(DeltaTitlePattern, DeltaTitlePatternAdmin)
admin.site.register(DeltaResolvedTitle, DeltaResolvedTitleAdmin)
admin.site.register(DeltaDivisionPattern, DeltaDivisionPatternAdmin)
admin.site.register(DumpUrl, DumpUrlAdmin)
admin.site.register(DeltaUrl, DeltaUrlAdmin)
admin.site.register(CuratedUrl, CuratedUrlAdmin)


@admin.register(ScraperConfigOverride)
class ScraperConfigOverrideAdmin(admin.ModelAdmin):
    """Curator-editable crawl overrides (WORKFLOW.md step 6)."""

    list_display = (
        "collection",
        "max_pages",
        "depth_limit",
        "delay",
        "concurrent_requests",
        "obey_robots",
        "include_subdomains",
    )
    search_fields = ("collection__name", "collection__config_folder")
    raw_id_fields = ("collection",)


@admin.register(ScrapeDispatch)
class ScrapeDispatchAdmin(admin.ModelAdmin):
    """Read-only dispatch log for debugging scrape runs."""

    list_display = ("collection", "dispatched_at", "ssm_command_id")
    search_fields = ("collection__name", "collection__config_folder", "ssm_command_id")
    list_filter = ("dispatched_at",)

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(IndexDispatch)
class IndexDispatchAdmin(admin.ModelAdmin):
    """Read-only dispatch log for debugging WEB_COSMOS index runs."""

    list_display = ("collection", "target", "run_id", "dispatched_at", "completed_at")
    search_fields = ("collection__name", "collection__config_folder", "run_id", "task_arn")
    list_filter = ("target", "dispatched_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

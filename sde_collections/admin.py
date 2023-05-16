from django import forms
from django.contrib import admin, messages
from django.db import models

from .models import CandidateURL, Collection, ExcludePattern
from .tasks import import_candidate_urls_task


@admin.action(description="Import metadata from Sinequa configs")
def import_sinequa_metadata(modeladmin, request, queryset):
    for collection in queryset.all():
        # eventually this needs to be done in celery
        collection.import_metadata_from_sinequa_config()
        messages.add_message(
            request,
            messages.INFO,
            f"Imported metadata for collection: {collection.name}",
        )


@admin.action(description="Export metadata to Sinequa config")
def export_sinequa_metadata(modeladmin, request, queryset):
    for collection in queryset.all():
        # eventually this needs to be done in celery
        collection.export_metadata_to_sinequa_config()
        messages.add_message(
            request,
            messages.INFO,
            f"Exported sinequa config for collection: {collection.name}",
        )


@admin.action(description="Generate candidate URLs")
def generate_candidate_urls(modeladmin, request, queryset):
    collection = queryset.first()
    collection.generate_candidate_urls()
    messages.add_message(
        request,
        messages.INFO,
        f"Started generating candidate URLs for: {collection.name}",
    )


@admin.action(description="Import candidate URLs")
def import_candidate_urls(modeladmin, request, queryset):
    import_candidate_urls_task.delay(list(queryset.values_list("id", flat=True)))
    collection_names = ", ".join(queryset.values_list("name", flat=True))
    messages.add_message(
        request,
        messages.INFO,
        f"Started importing URLs from S3 for: {collection_names}",
    )


class ExcludePatternInline(admin.TabularInline):
    model = ExcludePattern
    extra = 1
    formfield_overrides = {
        models.TextField: {"widget": forms.Textarea(attrs={"rows": 2, "cols": 40})},
    }


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
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
                    "tree_root",
                    "document_type",
                    "update_frequency",
                    "source",
                    "turned_on",
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
        "config_folder",
        "url",
        "division",
        "new_collection",
    )
    list_filter = (
        "division",
        "turned_on",
        "source",
        "document_type",
        "delete",
    )
    search_fields = ("name", "url")
    # list_per_page = 300
    actions = [
        # import_sinequa_metadata,
        # export_sinequa_metadata,
        # generate_candidate_urls,
        import_candidate_urls,
    ]
    ordering = ("cleaning_order",)
    inlines = [ExcludePatternInline]


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


class CandidateURLAdmin(admin.ModelAdmin):
    """Admin View for CandidateURL"""

    list_display = ("url", "scraped_title", "collection")
    list_filter = ("collection",)


admin.site.register(CandidateURL, CandidateURLAdmin)

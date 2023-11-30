import csv

from django.contrib import admin, messages
from django.http import HttpResponse

from .models.candidate_url import CandidateURL
from .models.collection import Collection
from .models.pattern import IncludePattern, TitlePattern
from .tasks import import_candidate_urls_from_api


@admin.action(description="Download candidate URLs as csv")
def download_candidate_urls_as_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="candidate_urls.csv"'

    writer = csv.writer(response)

    if len(queryset) > 1:
        messages.add_message(
            request, messages.ERROR, "You can only export one collection at a time."
        )
        return

    urls = CandidateURL.objects.filter(collection=queryset.first()).values_list(
        "url", flat=True
    )

    # Write your headers here
    writer.writerow(["candidate_url"])
    for url in urls:
        writer.writerow([url])

    return response


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


def import_candidate_urls_from_api_caller(modeladmin, request, queryset, server_name):
    id_list = queryset.values_list("id", flat=True)
    if len(id_list) > 1:
        messages.add_message(
            request,
            messages.ERROR,
            "We can only import one collection at a time using the admin action."
            " Consider using the django shell for bulk imports.",
        )
        return
    import_candidate_urls_from_api.delay(
        collection_ids=list(queryset.values_list("id", flat=True)),
        server_name=server_name,
    )
    collection_names = ", ".join(queryset.values_list("name", flat=True))
    messages.add_message(
        request,
        messages.INFO,
        f"Started importing URLs from the API for: {collection_names} from {server_name.title()}",
    )


@admin.action(description="Import candidate URLs from Test")
def import_candidate_urls_test(modeladmin, request, queryset):
    import_candidate_urls_from_api_caller(modeladmin, request, queryset, "test")


@admin.action(description="Import candidate URLs from Production")
def import_candidate_urls_production(modeladmin, request, queryset):
    import_candidate_urls_from_api_caller(modeladmin, request, queryset, "production")


@admin.action(description="Import candidate URLs from Secret Test")
def import_candidate_urls_secret_test(modeladmin, request, queryset):
    import_candidate_urls_from_api_caller(modeladmin, request, queryset, "secret_test")


@admin.action(description="Import candidate URLs from Secret Production")
def import_candidate_urls_secret_production(modeladmin, request, queryset):
    import_candidate_urls_from_api_caller(
        modeladmin, request, queryset, "secret_production"
    )


class ExportCsvMixin:
    def export_as_csv(self, request, queryset):
        meta = self.model._meta
        field_names = [field.name for field in meta.fields]

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename={meta}.csv"
        writer = csv.writer(response)

        writer.writerow(field_names)
        for obj in queryset:
            writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "Export selected as csv"


class UpdateConfigMixin:
    def update_config(self, request, queryset):
        for collection in queryset:
            collection.update_existing_config()

    update_config.short_description = "Update configs of selected"


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin, ExportCsvMixin, UpdateConfigMixin):
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
    readonly_fields = ("config_folder",)
    list_filter = ("division", "curation_status", "workflow_status", "turned_on")
    search_fields = ("name", "url", "config_folder")
    actions = [
        "export_as_csv",
        "update_config",
        download_candidate_urls_as_csv,
        import_candidate_urls_test,
        import_candidate_urls_production,
        import_candidate_urls_secret_test,
        import_candidate_urls_secret_production,
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


class CandidateURLAdmin(admin.ModelAdmin):
    """Admin View for CandidateURL"""

    list_display = ("url", "scraped_title", "collection")
    list_filter = ("collection",)


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


admin.site.register(CandidateURL, CandidateURLAdmin)
admin.site.register(TitlePattern, TitlePatternAdmin)
admin.site.register(IncludePattern)

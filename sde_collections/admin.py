from django.contrib import admin
from treebeard.admin import TreeAdmin
from treebeard.forms import movenodeform_factory

from .models import CandidateURL, Collection


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
                )
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

    list_display = ("name", "config_folder", "url", "division", "turned_on")
    list_filter = (
        "division",
        "turned_on",
        "source",
        "document_type",
        "delete",
    )
    search_fields = ("name", "url")


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


class CandidateURLAdmin(TreeAdmin):
    """Admin View for CandidateURL"""

    form = movenodeform_factory(CandidateURL)
    list_display = ("url", "title", "excluded", "collection")
    list_filter = ("excluded", "collection")
    actions = [exclude_and_delete_children]


admin.site.register(CandidateURL, CandidateURLAdmin)

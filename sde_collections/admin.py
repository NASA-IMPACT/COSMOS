import os
import subprocess

import boto3
import botocore
from django import forms
from django.conf import settings
from django.contrib import admin, messages
from django.db import models

from .models import CandidateURL, Collection, ExcludePattern


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
    s3 = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    # collection.import_candidate_urls()
    if queryset.count() > 1:
        messages.add_message(
            request, messages.ERROR, "Please select only one collection"
        )
        return

    collection = queryset.first()

    try:
        s3.download_file(
            settings.AWS_STORAGE_BUCKET_NAME,
            f"static/scraped_urls/{collection.config_folder}/urls.json",
            "urls.json",
        )
    except botocore.exceptions.ClientError:
        messages.add_message(
            request,
            messages.ERROR,
            f"Could not find candidate URLs on the S3 bucket for: {collection.name}",
        )
        return

    subprocess.run("python manage.py loaddata urls.json", shell=True)

    os.remove("urls.json")

    messages.add_message(
        request,
        messages.INFO,
        f"Started importing candidate URLs for: {collection.name}",
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
        "config_folder",
        "url",
        "division",
        "new_collection",
        "cleaning_order",
        "candidate_urls_count",
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

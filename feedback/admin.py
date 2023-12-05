from django.contrib import admin

from .models import ContentCurationRequest, Feedback


@admin.register(Feedback)
class ContactFormAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "comments"]
    search_fields = ["name", "email"]
    list_filter = ["subject"]


@admin.register(ContentCurationRequest)
class ContentCurationRequestAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "email",
        "scientific_focus",
        "data_type",
        "data_link",
        "additional_info",
    ]
    search_fields = ["name", "scientific_focus", "data_type"]
    list_filter = ["scientific_focus", "data_type"]

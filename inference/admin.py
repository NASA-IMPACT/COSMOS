# inference/admin.py
from django.contrib import admin

from inference.models.inference import ExternalJob, InferenceJob, ModelVersion
from inference.models.inference_choice_fields import (
    ExternalJobStatus,
    InferenceJobStatus,
)


class ExternalJobInline(admin.TabularInline):
    model = ExternalJob
    extra = 0
    readonly_fields = ["status", "external_job_id", "created_at", "updated_at", "completed_at", "error_message"]
    can_delete = False
    fields = ["external_job_id", "status", "created_at", "updated_at", "completed_at", "error_message"]
    show_change_link = True


@admin.register(ModelVersion)
class ModelVersionAdmin(admin.ModelAdmin):
    list_display = ["api_identifier", "get_classification_type_display", "is_active", "description"]
    list_filter = ["classification_type", "is_active"]
    search_fields = ["api_identifier", "description"]
    actions = ["set_as_active"]

    def set_as_active(self, request, queryset):
        for model_version in queryset:
            model_version.set_as_active()
        self.message_user(request, "Selected model versions set as active.")

    set_as_active.short_description = "Set selected model versions as active"


@admin.register(InferenceJob)
class InferenceJobAdmin(admin.ModelAdmin):
    list_display = ["id", "collection", "model_version", "status_display", "created_at", "updated_at", "completed_at"]
    list_filter = ["status", "model_version__classification_type"]
    search_fields = ["collection__name", "model_version__api_identifier", "error_message"]
    readonly_fields = ["created_at", "updated_at", "completed_at", "status_display"]
    raw_id_fields = ["collection"]
    fields = [
        "collection",
        "model_version",
        "status",
        "status_display",
        "error_message",
        "created_at",
        "updated_at",
        "completed_at",
    ]
    inlines = [ExternalJobInline]
    actions = ["initiate_job", "refresh_status", "unload_model"]

    def status_display(self, obj):
        return obj.get_status_display()

    status_display.short_description = "Status"

    def initiate_job(self, request, queryset):
        for job in queryset.filter(status=InferenceJobStatus.QUEUED):
            job.initiate()
        self.message_user(request, "Selected jobs have been initiated.")

    initiate_job.short_description = "Initiate selected queued jobs"

    def refresh_status(self, request, queryset):
        for job in queryset.filter(status=InferenceJobStatus.PENDING):
            job.refresh_external_jobs_status_and_store_results()
            job.reevaluate_progress_and_update_status()
        self.message_user(request, "Status of selected pending jobs has been refreshed.")

    refresh_status.short_description = "Refresh status of selected pending jobs"

    def unload_model(self, request, queryset):
        for job in queryset:
            job.unload_model()
        self.message_user(request, "Models for selected jobs have been unloaded.")

    unload_model.short_description = "Unload models for selected jobs"


@admin.register(ExternalJob)
class ExternalJobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "inference_job",
        "external_job_id",
        "status_display",
        "created_at",
        "updated_at",
        "completed_at",
    ]
    list_filter = ["status", "inference_job__model_version__classification_type"]
    search_fields = ["external_job_id", "inference_job__collection__name", "error_message"]
    readonly_fields = ["created_at", "updated_at", "completed_at", "status_display"]
    fields = [
        "inference_job",
        "external_job_id",
        "status",
        "status_display",
        "url_ids",
        "results",
        "error_message",
        "created_at",
        "updated_at",
        "completed_at",
    ]
    actions = ["refresh_status"]

    def status_display(self, obj):
        return obj.get_status_display()

    status_display.short_description = "Status"

    def refresh_status(self, request, queryset):
        ongoing_statuses = [ExternalJobStatus.QUEUED, ExternalJobStatus.PENDING]
        for job in queryset.filter(status__in=ongoing_statuses):
            job.refresh_status_and_store_results()
            job.inference_job.reevaluate_progress_and_update_status()
        self.message_user(request, "Status of selected jobs has been refreshed.")

    refresh_status.short_description = "Refresh status of selected jobs"

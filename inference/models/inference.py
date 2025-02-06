from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone

from inference.models.inference_choice_fields import ClassificationType, JobStatus


class InferenceJob(models.Model):
    """
    Tracks an inference job for a collection of URLs.
    One InferenceJob can have multiple ExternalJobs (one per batch).
    """

    def get_model_identifier(self) -> str:
        """Get the API model identifier for this job's classification type"""
        if self.classification_type == ClassificationType.TDAMM:
            return "tdamm-classifier-v1"
        elif self.classification_type == ClassificationType.DIVISION:
            return "division-classifier-v1"
        raise ValueError(f"Unknown classification type: {self.classification_type}")

    def set_error(self, error_msg: str) -> None:
        """Set error message and mark as failed"""
        self.error_message = error_msg
        self.completed = True  # Mark as complete even though failed
        self.completed_at = timezone.now()
        self.save(update_fields=["error_message", "completed", "completed_at", "updated_at"])

    @property
    def is_active(self) -> bool:
        """Check if job still has active external jobs"""
        return (
            not self.completed and self.external_jobs.filter(status__in=[JobStatus.QUEUED, JobStatus.PENDING]).exists()
        )

    @property
    def has_errors(self) -> bool:
        """Check if job or any external jobs have errors"""
        return bool(self.error_message) or self.external_jobs.filter(status=JobStatus.FAILED).exists()

    def get_failed_jobs(self):
        """Return QuerySet of failed external jobs"""
        return self.external_jobs.filter(status=JobStatus.FAILED)

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="inference_jobs")

    classification_type = models.IntegerField(
        choices=ClassificationType.choices, help_text="Type of classification to perform"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    completed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["completed", "created_at"]),
            models.Index(fields=["collection", "completed"]),
        ]

    def __str__(self):
        return f"Job {self.id} - {self.collection} - {self.get_classification_type_display()}"

    def clean(self):
        """Ensure we don't have multiple active jobs for the same collection/type"""
        if self.pk is None:  # Only check on creation
            existing_active = InferenceJob.objects.filter(
                collection=self.collection, classification_type=self.classification_type, completed=False
            ).exists()
            if existing_active:
                raise ValidationError("An active job already exists for this collection and classification type")

    def check_completion(self):
        """
        Check if all ExternalJobs are completed and results stored.
        If so, mark the InferenceJob as completed.
        """
        incomplete_jobs = self.external_jobs.exclude(status=JobStatus.COMPLETED)
        if not incomplete_jobs.exists():
            self.completed = True
            self.completed_at = timezone.now()
            self.save()
            self.cleanup_external_jobs()

    def cleanup_external_jobs(self):
        """Delete all external jobs after completion"""
        if self.completed:
            self.external_jobs.all().delete()


class ExternalJob(models.Model):
    """
    Represents a batch job sent to the inference API.
    Multiple ExternalJobs can belong to one InferenceJob.
    """

    def set_error(self, error_msg: str) -> None:
        """Set error message and update status"""
        self.error_message = error_msg
        self.status = JobStatus.FAILED
        self.save(update_fields=["error_message", "status", "updated_at"])

    def set_status(self, status: JobStatus) -> None:
        """Update job status"""
        self.status = status
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_active(self) -> bool:
        """Check if job is currently processing"""
        return self.status in [JobStatus.QUEUED, JobStatus.PENDING]

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    inference_job = models.ForeignKey(InferenceJob, on_delete=models.CASCADE, related_name="external_jobs")

    external_job_id = models.CharField(max_length=255, help_text="Job ID returned by the inference API")

    status = models.IntegerField(choices=JobStatus.choices, default=JobStatus.QUEUED)

    batch_index = models.IntegerField(help_text="Index of this batch in the overall job")

    # Store URL IDs for this batch
    url_ids = models.JSONField(help_text="List of URL IDs included in this batch")

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["batch_index"]
        indexes = [
            models.Index(fields=["inference_job", "status"]),
            models.Index(fields=["external_job_id"]),
        ]
        constraints = [models.UniqueConstraint(fields=["inference_job", "batch_index"], name="unique_batch_per_job")]

    def __str__(self):
        return f"Batch {self.batch_index} of Job {self.inference_job_id}"

    def mark_completed(self):
        """Mark batch as completed and check parent job completion"""
        self.status = JobStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

        # Check if parent job is complete
        self.inference_job.check_completion()

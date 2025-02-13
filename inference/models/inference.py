# inference/models/inference.py
from django.db import models
from django.utils import timezone

from inference.models import ClassificationType, ExternalJobStatus, InferenceJobStatus
from inference.utils.batch import BatchConfig, BatchProcessor
from inference.utils.inference_api_client import InferenceAPIClient, ModelManager


class ModelVersion(models.Model):
    """
    Allows us to maintain tracking between multiple versions of a classification model.
    """

    api_identifier = models.CharField(max_length=255)
    description = models.TextField()
    classification_type = models.IntegerField(
        choices=ClassificationType.choices, help_text="Type of classification this model performs"
    )
    is_active = models.BooleanField(
        default=True, help_text="Whether this is the current active version for its classification type"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["classification_type", "is_active"],
                condition=models.Q(is_active=True),
                name="unique_active_version",
            )
        ]

    def __str__(self):
        return f"{self.get_classification_type_display()} - {self.api_identifier}"

    @classmethod
    def get_active_version(cls, classification_type: int) -> "ModelVersion":
        """Get the current active model version for a classification type."""
        return cls.objects.get(classification_type=classification_type, is_active=True)

    def set_as_active(self):
        """Set this version as the active one for its classification type."""
        # Deactivate other versions of this classification type
        ModelVersion.objects.filter(classification_type=self.classification_type, is_active=True).exclude(
            id=self.id
        ).update(is_active=False)

        # Set this one as active
        self.is_active = True
        self.save()


class InferenceJob(models.Model):
    """
    Tracks an inference job for a collection of URLs.
    One InferenceJob can have multiple ExternalJobs (one per batch).
    """

    collection = models.ForeignKey(
        "sde_collections.Collection", on_delete=models.CASCADE, related_name="inference_jobs"
    )
    model_version = models.ForeignKey(
        ModelVersion,
        on_delete=models.PROTECT,  # Prevent deletion of ModelVersions that have associated jobs
        related_name="inference_jobs",
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    status = models.IntegerField(choices=InferenceJobStatus.choices, default=InferenceJobStatus.QUEUED)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["collection", "model_version"],
                condition=models.Q(status__in=[InferenceJobStatus.QUEUED, InferenceJobStatus.PENDING]),
                name="unique_active_job",
            )
        ]

    def __str__(self):
        return f"Job {self.id} - {self.collection} - {self.model_version}"

    @property
    def is_ongoing(self) -> bool:
        """Check if job still has active external jobs"""
        return self.external_jobs.filter(status__in=[ExternalJobStatus.QUEUED, ExternalJobStatus.PENDING]).exists()

    def get_failed_jobs(self):
        """Return QuerySet of failed external jobs"""
        return self.external_jobs.filter(
            status__in=[
                ExternalJobStatus.FAILED,
                ExternalJobStatus.CANCELLED,
                ExternalJobStatus.NOT_FOUND,
                ExternalJobStatus.UNKNOWN,
            ]
        )

    def check_completion(self):
        """
        Check if all ExternalJobs are completed and results stored.
        If so, mark the InferenceJob as completed.
        """
        incomplete_jobs = self.external_jobs.exclude(status=ExternalJobStatus.COMPLETED)
        if not incomplete_jobs.exists():
            self.status = InferenceJobStatus.COMPLETED
            self.completed_at = timezone.now()
            self.save()

    def cleanup_external_jobs(self):
        """Delete all external jobs"""
        if self.completed:
            self.external_jobs.all().delete()

    def set_error(self, error_msg: str) -> None:
        """Set general error and mark job as failed"""
        self.error_message = error_msg
        self.status = InferenceJobStatus.FAILED
        self.completed_at = timezone.now()
        self.save(update_fields=["error_message", "status", "completed_at", "updated_at"])

    def initiate(self) -> None:
        """Initialize job and create batches"""
        try:
            # Load model
            model_manager = ModelManager(InferenceAPIClient(), self.model_version.api_identifier)

            if not model_manager.ensure_model_loaded():
                # TODO: shouldn't we be getting an exact error out of the api client that we can store?
                self.set_error("Failed to load model")
                return

            # Create batches
            batch_processor = BatchProcessor(BatchConfig())
            urls = self.collection.curated_urls.all()
            batches = batch_processor.create_batches(urls)

            # Create external jobs for batches
            for batch in batches:
                self.create_external_job(batch)

            if not self.external_jobs.exists():
                self.set_error("No batches created")
                return

            self.status = InferenceJobStatus.PENDING
            self.save()

        except Exception as e:
            self.set_error(str(e))

    def create_external_job(self, batch_data) -> "ExternalJob":
        """Create and submit an external job for a batch"""
        try:
            api_client = InferenceAPIClient()

            # Submit batch to API using model version identifier
            job_id = api_client.submit_batch(self.model_version.api_identifier, batch_data)

            if not job_id:
                # TODO: can't we get an exact error out of the api client?
                self.set_error("Failed to get job ID from API")
                return None

            # Create external job record
            return ExternalJob.objects.create(
                inference_job=self,
                external_job_id=job_id,
                url_ids=[item["url_id"] for item in batch_data],
                status=ExternalJobStatus.QUEUED,
            )

        except Exception as e:
            self.set_error(f"Failed to create external job: {str(e)}")
            return None

    def process_external_jobs(self) -> None:
        """Process all pending external jobs"""
        pending_jobs = self.external_jobs.filter(status__in=[ExternalJobStatus.QUEUED, ExternalJobStatus.PENDING])

        for external_job in pending_jobs:
            external_job.process()

    def evaluate_status(self) -> None:
        """Evaluate overall job status and handle completion"""

        if self.is_ongoing:
            self.status = InferenceJobStatus.PENDING
        else:
            failed_jobs = self.get_failed_jobs()
            if failed_jobs.exists():
                self.status = InferenceJobStatus.FAILED
            else:
                self.status = InferenceJobStatus.COMPLETED
                self.cleanup()

            self.completed_at = timezone.now()

        self.save()

    def cleanup(self) -> None:
        """Handle cleanup after job completion"""
        try:
            # Unload model if no other jobs need it
            if not InferenceJob.objects.filter(
                model_version=self.model_version, status=InferenceJobStatus.PENDING
            ).exists():
                model_manager = ModelManager(InferenceAPIClient(), self.model_version.api_identifier)
                model_manager.api_client.unload_model(self.model_version.api_identifier)

        except Exception as e:
            self.set_error(f"Cleanup error: {str(e)}")


class ExternalJob(models.Model):
    """
    Represents a batch job sent to the inference API.
    Multiple ExternalJobs can belong to one InferenceJob.
    """

    inference_job = models.ForeignKey(InferenceJob, on_delete=models.CASCADE, related_name="external_jobs")
    external_job_id = models.CharField(max_length=255, help_text="Job ID returned by the inference API")

    url_ids = models.JSONField(help_text="List of URL IDs included in this batch")

    status = models.IntegerField(choices=ExternalJobStatus.choices, default=ExternalJobStatus.QUEUED)
    results = models.JSONField(blank=True)
    error_message = models.TextField(blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def set_status(self, status: ExternalJobStatus) -> None:
        """Update job status"""
        self.status = status
        self.save(update_fields=["status", "updated_at"])

    @property
    def is_ongoing(self) -> bool:
        """Check if job is currently processing"""
        return self.status in [ExternalJobStatus.QUEUED, ExternalJobStatus.PENDING]

    def mark_completed(self):
        """Mark batch as completed and check parent job completion"""
        self.status = ExternalJobStatus.COMPLETED
        self.completed_at = timezone.now()
        self.save()

    def process(self) -> None:
        """Process this external job and update status/results"""
        try:
            api_client = InferenceAPIClient()
            model_version = ModelVersion.objects.get(classification_type=self.inference_job.classification_type)

            response = api_client.get_job_status(model_version.api_identifier, self.external_job_id)

            # Update status
            new_status = ExternalJobStatus.from_api_status(response["status"])
            self.status = new_status

            # Handle completion or failure
            if new_status == ExternalJobStatus.COMPLETED:
                self.store_results(response.get("results"))
            elif new_status in [ExternalJobStatus.FAILED, ExternalJobStatus.CANCELLED]:
                self.set_error(response.get("message", ""))

            self.save()

        except Exception as e:
            self.set_error(f"Processing error: {str(e)}")

    def store_results(self, results) -> None:
        """Store results and mark as completed"""
        try:
            self.results = results
            self.completed_at = timezone.now()
            self.save()

        except Exception as e:
            self.set_error(f"Error storing results: {str(e)}")

    def set_error(self, error_msg: str) -> None:
        """Set error message and mark as failed"""
        self.error_message = error_msg
        self.status = ExternalJobStatus.FAILED
        self.save(update_fields=["error_message", "status", "updated_at"])

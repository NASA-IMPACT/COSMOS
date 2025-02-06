# sde_collections/tasks/inference.py
from time import sleep
from typing import Any

import requests
from celery import shared_task
from django.conf import settings

from ..models.inference import ClassificationTypes, InferenceJob, InferenceStatusChoices


class InferenceJobProcessor:
    """Handles the lifecycle of an inference job"""

    def __init__(self, job_id: int):
        self.job = InferenceJob.objects.get(id=job_id)
        self.model_identifier = ClassificationTypes.get_model_identifier(self.job.classification_type)
        if not self.model_identifier:
            self.set_failed("Invalid classification type")

    def set_failed(self, error_msg: str) -> None:
        """Set job to failed state with error message"""
        self.job.set_error(error_msg)

    def is_failed(self) -> bool:
        """Check if job is in failed state"""
        return self.job.status == InferenceStatusChoices.FAILED

    def make_api_request(self, method: str, endpoint: str, **kwargs) -> dict[str, Any] | None:
        """Make a request to the inference API with error handling"""
        if self.is_failed():
            return None

        try:
            url = f"{settings.INFERENCE_API_URL}/api/v1/inferencers/{endpoint}"
            response = requests.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            self.set_failed(f"API request failed: {str(e)}")
            return None

    def get_model_status(self) -> str | None:
        """
        Get current model status from API
        Returns None if request fails or job is already failed
        """
        if self.is_failed():
            return None

        response = self.make_api_request("GET", f"{self.model_identifier}/status")
        if not response:
            return None

        return response.get("status", "unknown")

    def request_model_load(self) -> bool:
        """
        Request model to be loaded
        Returns True if request succeeds, False otherwise
        """
        if self.is_failed():
            return False

        response = self.make_api_request("POST", f"{self.model_identifier}/load")
        return response is not None

    def request_model_unload(self) -> bool:
        """
        Request model to be unloaded
        Returns True if request succeeds, False otherwise
        """
        if self.is_failed():
            return False

        response = self.make_api_request("POST", f"{self.model_identifier}/unload")
        return response is not None

    def ensure_model_loaded(self, max_retries: int = 5, retry_delay: int = 30) -> bool:
        """
        Ensure model is loaded and ready for inference
        Returns True if model is loaded, False if failed or max retries exceeded
        """
        if self.is_failed():
            return False

        retries = 0
        while retries < max_retries:
            status = self.get_model_status()
            if not status:  # API request failed
                return False

            if status == "loaded":
                return True

            if status in ["unloaded", "failed", "unknown"]:
                if not self.request_model_load():
                    return False

            if status == "loading":
                retries += 1
                if retries >= max_retries:
                    self.set_failed("Timeout waiting for model to load")
                    return False
                sleep(retry_delay)

        return False

    def process_batch(self, texts: list[str]) -> bool:
        """
        Process a batch of texts
        Returns True if batch was submitted successfully, False otherwise
        """
        if self.is_failed():
            return False

        response = self.make_api_request("POST", f"{self.model_identifier}/jobs", json={"input_data": texts})

        if response and "job_id" in response:
            self.job.external_job_id = response["job_id"]
            self.job.status = InferenceStatusChoices.IN_PROGRESS
            self.job.save(update_fields=["external_job_id", "status", "updated_at"])
            return True

        return False

    def process(self) -> None:
        """Process the entire inference job"""
        # Exit early if job is already failed
        if self.is_failed():
            return

        # Ensure model is loaded
        if not self.ensure_model_loaded():
            return

        # Get URLs with full text in batches
        urls = self.job.collection.curated_urls.exclude(scraped_text="")
        if not urls.exists():
            self.set_failed("No URLs with text content found")
            return

        # Process in batches of 100
        batch_size = 100
        for i in range(0, urls.count(), batch_size):
            batch = urls[i : i + batch_size]
            texts = [url.scraped_text for url in batch]

            if self.process_batch(texts):
                # Start polling for results and exit
                poll_inference_results.delay(self.job.id)
                return
            elif self.is_failed():
                return

    def check_results(self) -> None:
        """Check the status of the inference job"""
        if self.is_failed():
            return

        response = self.make_api_request("GET", f"{self.model_identifier}/jobs/{self.job.external_job_id}")

        if not response:
            return

        status = response.get("status")

        if status == "completed":
            self.job.results = response.get("results")
            self.job.status = InferenceStatusChoices.COMPLETED
            self.job.save()

            # Update collection/URLs with results
            update_collection_with_results.delay(self.job.id)

            # Try to unload model since we're done
            self.request_model_unload()
        elif status in ["failed", "cancelled", "not_found"]:
            error_msg = response.get("error", "Job failed without specific error")
            self.set_failed(error_msg)


@shared_task
def process_inference_job(job_id: int):
    """Process a single inference job"""
    processor = InferenceJobProcessor(job_id)
    processor.process()


@shared_task
def schedule_inference_jobs():
    """Schedule queued inference jobs"""
    # Only process one job at a time
    job = InferenceJob.objects.filter(status=InferenceStatusChoices.QUEUED).first()
    if job:
        process_inference_job.delay(job.id)


@shared_task(bind=True)
def poll_inference_results(self, job_id: int):
    """Poll the inference API for results"""
    processor = InferenceJobProcessor(job_id)
    processor.check_results()

    # If job isn't complete or failed, schedule another check
    if processor.job.status == InferenceStatusChoices.IN_PROGRESS:
        poll_inference_results.apply_async(args=[job_id], countdown=300)  # 5 minutes


@shared_task
def update_collection_with_results(job_id: int):
    """Update collection metadata with inference results"""
    job = InferenceJob.objects.get(id=job_id)
    results = job.results

    if not results:
        return

    urls = job.collection.curated_urls.exclude(scraped_text="")

    if job.classification_type == ClassificationTypes.TDAMM:
        # Update TDAMM classifications
        for url, classifications in zip(urls, results):
            url.tdamm_classifications = classifications
            url.save()
    elif job.classification_type == ClassificationTypes.DIVISION:
        # Update division classification
        for url, division in zip(urls, results):
            url.division = division
            url.save()

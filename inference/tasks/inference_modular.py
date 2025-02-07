# sde_collections/tasks/inference.py
import logging
from dataclasses import dataclass
from time import time

import requests
from celery import shared_task
from django.conf import settings
from django.db.models import QuerySet

from ..models.inference import ClassificationType, ExternalJob, InferenceJob, JobStatus

logger = logging.getLogger(__name__)


@dataclass
class BatchConfig:
    """Configuration for batch processing"""

    batch_size: int = 100  # URLs per batch
    max_text_length: int = 10000  # Max chars for full_text
    timeout: int = 150  # API timeout in seconds


class InferenceAPIClient:
    """Handles all direct interactions with the Inference API"""

    def __init__(self, base_url: str = settings.INFERENCE_API_URL, timeout: int = 150):
        self.base_url = base_url
        self.timeout = timeout

    def make_api_request(self, method: str, endpoint: str, **kwargs) -> dict | None:
        """Make a request to the inference API with error handling"""
        try:
            url = f"{self.base_url}/api/v1/inferencers/{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            logger.exception(f"API request failed: {str(e)}")
            return None

    def load_model(self, model_identifier: str) -> bool:
        """Request model loading from API"""
        response = self.make_api_request("POST", f"{model_identifier}/load")
        return response is not None

    def unload_model(self, model_identifier: str) -> bool:
        """Request model unloading from API"""
        response = self.make_api_request("POST", f"{model_identifier}/unload")
        return response is not None

    def check_model_status(self, model_identifier: str) -> str:
        """Check if model is loaded and ready"""
        response = self.make_api_request("GET", f"{model_identifier}/status")
        return response.get("status", "unknown") if response else "unknown"

    def submit_batch(self, model_identifier: str, batch_data: list[dict]) -> str | None:
        """Submit a batch of URLs for inference"""
        # Extract just the text data for the model
        text_data = [item["text"] for item in batch_data]
        response = self.make_api_request("POST", f"{model_identifier}/jobs", json={"input_data": text_data})
        return response.get("job_id") if response else None

    def get_job_status(self, model_identifier: str, job_id: str) -> dict:
        """Check status of a submitted job"""
        return self.make_api_request("GET", f"{model_identifier}/jobs/{job_id}")


class ModelManager:
    """Handles model loading/unloading and ensures right model is active"""

    def __init__(self, api_client: InferenceAPIClient):
        self.api_client = api_client
        self.current_model = None

    def ensure_model_loaded(self, model_identifier: str, max_retries: int = 5, retry_delay: int = 30) -> bool:
        """Make sure the right model is loaded, unloading others if needed"""
        # Unload different model if loaded
        if self.current_model and self.current_model != model_identifier:
            if not self.api_client.unload_model(self.current_model):
                return False
            self.current_model = None

        retries = 0
        while retries < max_retries:
            status = self.api_client.check_model_status(model_identifier)

            if status == "loaded":
                self.current_model = model_identifier
                return True

            if status in ["unloaded", "failed", "unknown"]:
                if not self.api_client.load_model(model_identifier):
                    return False

            retries += 1
            if retries < max_retries:
                time.sleep(retry_delay)

        return False


class BatchProcessor:
    """Handles batching of URLs and preparation of data for API"""

    def __init__(self, config: BatchConfig):
        self.config = config

    def prepare_url_data(self, url) -> dict:
        """Prepare single URL data for API"""
        return {
            "url_id": url.id,
            "text": url.scraped_text[: self.config.max_text_length],
            "metadata": {"title": url.scraped_title, "url": url.url},
        }

    def create_batches(self, urls: QuerySet) -> list[list[dict]]:
        """Split URLs into API-friendly batches"""
        batches = []
        current_batch = []

        for url in urls:
            if len(current_batch) >= self.config.batch_size:
                batches.append(current_batch)
                current_batch = []
            current_batch.append(self.prepare_url_data(url))

        if current_batch:
            batches.append(current_batch)

        return batches


class InferenceJobProcessor:
    """Main orchestrator for processing inference jobs"""

    def __init__(
        self,
        job_id: int,
        api_client: InferenceAPIClient | None = None,
        model_manager: ModelManager | None = None,
        batch_processor: BatchProcessor | None = None,
    ):
        self.job = InferenceJob.objects.get(id=job_id)
        self.api_client = api_client or InferenceAPIClient()
        self.model_manager = model_manager or ModelManager(self.api_client)
        self.batch_processor = batch_processor or BatchProcessor(BatchConfig())

    def process_job(self) -> None:
        """Process a single inference job"""
        try:
            # Get model identifier for classification type
            model_id = self.job.get_model_identifier()

            # Ensure model is loaded
            if not self.model_manager.ensure_model_loaded(model_id):
                raise Exception(f"Failed to load model {model_id}")

            # Get unprocessed URLs
            urls = self.get_unprocessed_urls()
            if not urls.exists():
                raise Exception("No URLs with text content found")

            # Create and submit batches
            batches = self.batch_processor.create_batches(urls)
            for idx, batch in enumerate(batches):
                if not self.submit_batch(batch, idx):
                    raise Exception(f"Failed to submit batch {idx}")

        except Exception as e:
            self.job.set_error(str(e))
            logger.exception(f"Error processing job {self.job.id}")

    def submit_batch(self, batch_data: list[dict], batch_index: int) -> bool:
        """Submit a batch and create ExternalJob"""
        try:
            # Submit to API
            job_id = self.api_client.submit_batch(self.job.get_model_identifier(), batch_data)
            if not job_id:
                return False

            # Create ExternalJob
            ExternalJob.objects.create(
                inference_job=self.job,
                external_job_id=job_id,
                batch_index=batch_index,
                url_ids=[d["url_id"] for d in batch_data],
            )
            return True

        except Exception as e:
            logger.exception(f"Error submitting batch {batch_index} for job {self.job.id}, error: {str(e)}")
            return False

    def get_unprocessed_urls(self) -> QuerySet:
        """Get URLs that haven't been processed yet"""
        processed_ids = set()
        for external_job in self.job.external_jobs.all():
            processed_ids.update(external_job.url_ids)

        return self.job.collection.delta_urls.exclude(id__in=processed_ids).exclude(scraped_text="")

    def check_results(self) -> None:
        """Check and process results for all external jobs"""
        for external_job in self.job.external_jobs.filter(status__in=[JobStatus.QUEUED, JobStatus.PENDING]):
            response = self.api_client.get_job_status(self.job.get_model_identifier(), external_job.external_job_id)

            if not response:
                continue

            status = JobStatus.from_api_status(response.get("status", "unknown"))

            if status == JobStatus.COMPLETED:
                results = response.get("results", [])
                ResultProcessor.store_results(external_job, results)
            elif status in [JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.NOT_FOUND]:
                error_msg = response.get("error", "Job failed without specific error")
                external_job.set_error(error_msg)


class ResultProcessor:
    """Handles processing and storing of inference results"""

    @classmethod
    def store_results(cls, external_job: ExternalJob, results: list[dict]) -> None:
        """Store results in database using PairedFieldDescriptor"""
        try:
            # Get URLs for this batch
            urls = external_job.inference_job.collection.delta_urls.filter(id__in=external_job.url_ids)

            # Create URL ID to result mapping
            result_map = {r["url_id"]: r["classifications"] for r in results}

            # Update URLs
            for url in urls:
                if url.id in result_map:
                    if external_job.inference_job.classification_type == ClassificationType.TDAMM:
                        url.tdamm_tag_ml = result_map[url.id]
                    elif external_job.inference_job.classification_type == ClassificationType.DIVISION:
                        url.division_ml = result_map[url.id]
                    url.save()

            # Mark job as completed
            external_job.mark_completed()

        except Exception as e:
            external_job.set_error(f"Error storing results: {str(e)}")
            logger.exception(f"Error storing results for job {external_job.id}")


# Celery Tasks


@shared_task
def process_inference_job(job_id: int):
    """Process a single inference job"""
    processor = InferenceJobProcessor(job_id)
    processor.process_job()


@shared_task
def schedule_inference_jobs():
    """Schedule queued inference jobs"""
    # Only process one job at a time
    job = InferenceJob.objects.filter(completed=False).first()
    if job:
        process_inference_job.delay(job.id)


@shared_task(bind=True)
def poll_inference_results(self, job_id: int):
    """Poll the inference API for results"""
    processor = InferenceJobProcessor(job_id)
    processor.check_results()

    # Continue polling if job has active external jobs
    if processor.job.is_active:
        poll_inference_results.apply_async(args=[job_id], countdown=300)  # 5 minutes

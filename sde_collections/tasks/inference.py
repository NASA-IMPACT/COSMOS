# sde_collections/tasks/inference.py
import requests
from celery import shared_task
from django.conf import settings

from ..models.inference import ClassificationTypes, InferenceJob, InferenceStatusChoices


def ensure_model_loaded(model_identifier: str) -> bool:
    """Ensure the model is loaded and ready for inference"""
    # Check current status
    response = requests.get(f"{settings.INFERENCE_API_URL}/api/v1/inferencers/{model_identifier}/status")
    if response.status_code != 200:
        return False

    status = response.json().get("status")
    if status == "loaded":
        return True

    # If not loaded, request loading
    if status in ["unloaded", "failed", "unknown"]:
        response = requests.post(f"{settings.INFERENCE_API_URL}/api/v1/inferencers/{model_identifier}/load")
        return response.status_code == 200

    return False


@shared_task
def process_inference_job(job_id: int):
    """Process a single inference job"""
    job = InferenceJob.objects.get(id=job_id)
    collection = job.collection

    # Get model identifier based on classification type
    model_identifier = ClassificationTypes.get_model_identifier(job.classification_type)
    if not model_identifier:
        job.status = InferenceStatusChoices.FAILED
        job.save()
        return

    # Ensure model is loaded
    if not ensure_model_loaded(model_identifier):
        job.status = InferenceStatusChoices.FAILED
        job.save()
        return

    # Get URLs with full text in batches
    urls = collection.curated_urls.exclude(scraped_text="")

    # Process in batches of 100
    batch_size = 100
    for i in range(0, urls.count(), batch_size):
        batch = urls[i : i + batch_size]
        texts = [url.scraped_text for url in batch]

        # Submit inference job
        response = requests.post(
            f"{settings.INFERENCE_API_URL}/api/v1/inferencers/{model_identifier}/jobs", json={"input_data": texts}
        )

        if response.status_code == 200:
            job.external_job_id = response.json()["job_id"]
            job.status = InferenceStatusChoices.IN_PROGRESS
            job.save()

            # Start polling for results
            poll_inference_results.delay(job.id)
        else:
            job.status = InferenceStatusChoices.FAILED
            job.save()
            return


@shared_task
def schedule_inference_jobs():
    jobs = InferenceJob.objects.filter(status=InferenceStatusChoices.QUEUED)
    for job in jobs:
        process_inference_job.delay(job.id)


@shared_task
def poll_inference_results(job_id: int):
    """Poll the inference API for results"""
    job = InferenceJob.objects.get(id=job_id)
    model_identifier = ClassificationTypes.get_model_identifier(job.classification_type)
    if not model_identifier:
        job.status = InferenceStatusChoices.FAILED
        job.save()
        return

    response = requests.get(
        f"{settings.INFERENCE_API_URL}/api/v1/inferencers/{model_identifier}/jobs/{job.external_job_id}"
    )

    if response.status_code == 200:
        data = response.json()
        if data["status"] == "completed":
            job.results = data.get("results")
            job.status = InferenceStatusChoices.COMPLETED
            job.save()

            # Update collection/URLs with results
            update_collection_with_results.delay(job.id)
        elif data["status"] in ["failed", "cancelled", "not_found"]:
            job.status = InferenceStatusChoices.FAILED
            job.save()
        else:
            # Retry after delay if still processing
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

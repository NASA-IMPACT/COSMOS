# inference/tests/test_inference_integration.py
# docker-compose -f local.yml run --rm django pytest inference/tests/test_inference_integration.py
import pytest

from inference.models.inference import ExternalJob, InferenceJob, ModelVersion
from inference.models.inference_choice_fields import (
    ClassificationType,
    ExternalJobStatus,
    InferenceJobStatus,
)
from inference.utils.inference_api_client import InferenceAPIClient, JobStatusEnum
from sde_collections.tests.factories import CollectionFactory, DumpUrlFactory

# Configuration
API_BASE = "http://host.docker.internal:8000"


@pytest.fixture
def api_client():
    """Provide a configured API client"""
    return InferenceAPIClient(base_url=API_BASE, timeout=10)


@pytest.fixture
def check_api_health(api_client):
    """Check if the API is healthy and skip all tests if not"""
    if not api_client.check_health():
        pytest.skip("API is not healthy, skipping all tests")


@pytest.fixture
def require_available_model(api_client, check_api_health):
    """Ensure at least one model is available, or skip all tests"""
    available_models = api_client.get_available_inferencers()

    # Check if we got a valid response with models
    if (
        isinstance(available_models, dict)
        and not ("status" in available_models and available_models.get("status") == JobStatusEnum.FAILED)
        and available_models
    ):
        # Return the available model names for other fixtures to use
        return list(available_models.keys())

    # If no models found, skip all tests
    pytest.skip("No available inference models found, skipping all tests")


@pytest.fixture
def model_name(require_available_model):
    """Return the first available model name"""
    return require_available_model[0]


@pytest.fixture
def model_version(model_name):
    """Create a model version for testing"""
    model_version = ModelVersion.objects.create(
        api_identifier=model_name,
        description="Test model version",
        classification_type=ClassificationType.TDAMM,
        is_active=True,
    )
    return model_version


@pytest.fixture
def clean_environment(api_client):
    """Ensure no models are loaded before and after tests"""
    api_client.unload_all_models()
    yield
    api_client.unload_all_models()


@pytest.fixture
def loaded_model(api_client, clean_environment, model_name):
    """Provide a test with a loaded model"""
    success = api_client.load_model(model_name)
    assert success, f"Failed to load test model {model_name}"
    return model_name


@pytest.fixture
def collection():
    """Create a test collection"""
    return CollectionFactory()


@pytest.fixture
def dump_urls(collection):
    """Create dump URLs for the test collection"""
    urls = []
    for i in range(5):
        urls.append(DumpUrlFactory(collection=collection))
    return urls


@pytest.fixture
def many_dump_urls(collection):
    """Create many dump URLs to ensure multiple batches are created"""
    urls = []
    # Create enough URLs to ensure multiple batches
    # The BatchProcessor's default max_batch_text_length is 10000
    for i in range(20):
        # Create URLs with varying text lengths to trigger multiple batches
        text_length = 2000 if i % 3 == 0 else 500
        urls.append(DumpUrlFactory(collection=collection, scraped_text="x" * text_length))
    return urls


@pytest.fixture
def inference_job(collection, model_version):
    """Create an inference job for testing"""
    return InferenceJob.objects.create(
        collection=collection, model_version=model_version, status=InferenceJobStatus.QUEUED
    )


@pytest.mark.django_db
def test_create_external_job(loaded_model, inference_job, api_client):
    """
    Test the _create_external_job method.

    This test verifies:
    1. An external job can be created
    2. The external job has the correct attributes
    3. We can ping the API with the job ID
    4. The job eventually reaches a terminal state
    """
    # Prepare batch data similar to what BatchProcessor would produce
    batch_data = [
        {"url_id": 1, "text": "Test text 1", "metadata": {"title": "Test title 1", "url": "http://example.com/1"}},
        {"url_id": 2, "text": "Test text 2", "metadata": {"title": "Test title 2", "url": "http://example.com/2"}},
    ]

    # Call the method directly
    external_job = inference_job._create_external_job(batch_data, api_client)

    # Verify an external job was created
    assert external_job is not None
    assert external_job.inference_job_id == inference_job.id
    assert external_job.external_job_id is not None
    assert external_job.url_ids == [1, 2]

    # Verify we can ping the API with the job ID
    job_status = api_client.get_job_status(inference_job.model_version.api_identifier, external_job.external_job_id)
    assert job_status is not None
    assert "status" in job_status

    # Refresh external job to check for completion
    external_job.refresh_status_and_store_results()
    external_job.refresh_from_db()

    # The job should eventually complete (this might take time)
    assert external_job.status in [ExternalJobStatus.COMPLETED, ExternalJobStatus.FAILED, ExternalJobStatus.CANCELLED]

    # If job completed, check for results
    if external_job.status == ExternalJobStatus.COMPLETED:
        assert external_job.results is not None


@pytest.mark.django_db
def test_initiate(inference_job, many_dump_urls, api_client):
    """
    Test the initiate method creates multiple external jobs.

    This test verifies:
    1. The initiate method changes the job status to PENDING
    2. Multiple external jobs are created due to batching
    3. Each external job has a valid job ID
    4. We can ping the API for each job
    """
    # Make sure the parent collection has the dump URLs
    assert inference_job.collection.dump_urls.count() == len(many_dump_urls)

    # Note: There appears to be a potential parameter naming mismatch in the InferenceJob.initiate
    # method vs. what InferenceAPIClient expects. The client expects 'base_url' while the job
    # method uses 'inference_api_url'. For testing, we're passing API_BASE.
    inference_job.initiate(inference_api_url=API_BASE)

    # Verify job status changed to PENDING
    inference_job.refresh_from_db()
    assert inference_job.status == InferenceJobStatus.PENDING

    # Check that external jobs were created
    external_jobs = ExternalJob.objects.filter(inference_job=inference_job)
    assert external_jobs.exists()

    # There should be multiple external jobs due to the batch size
    assert external_jobs.count() > 1

    # Verify each external job has a valid job ID
    for job in external_jobs:
        assert job.external_job_id is not None

        # Verify we can ping the API for each job
        job_status = api_client.get_job_status(inference_job.model_version.api_identifier, job.external_job_id)
        assert job_status is not None
        assert "status" in job_status

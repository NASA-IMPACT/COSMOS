# docker-compose -f local.yml run --rm django pytest -s inference/tests/local_test_inference_integration.py
"""
This is a test designed to be run on a local machine which has the inference pipeline running,
    to ensure that the pipeline is functioning correctly.
It also serves as a guide for how to send requests to the inference pipeline.
"""
import time
from typing import Any

import pytest
import requests

from inference.models import (
    ClassificationType,
    ExternalJobStatus,
    InferenceJob,
    InferenceJobStatus,
    ModelVersion,
)
from inference.utils.batch import BatchConfig, BatchProcessor
from inference.utils.inference_api_client import ModelStatusEnum


@pytest.fixture
def model_version(db):
    """Create a test model version."""
    return ModelVersion.objects.create(
        api_identifier="DC",  # Division Classifier
        description="Test Division Classifier Model",
        classification_type_id=ClassificationType.DIVISION,
    )


@pytest.fixture
def test_data() -> list[dict[str, Any]]:
    """Sample test data for inference."""
    return [
        {
            "url_id": 1,
            "text": "This is a sample text about astrophysics and space exploration.",
            "metadata": {"title": "Astrophysics Research", "url": "http://example.com/doc1"},
        },
        {
            "url_id": 2,
            "text": "The sun is a star, and it is the center of our solar system.",
            "metadata": {"title": "Solar System", "url": "http://example.com/doc2"},
        },
        {
            "url_id": 3,
            "text": "The Earth is our home planet in the solar system.",
            "metadata": {"title": "Earth Science", "url": "http://example.com/doc3"},
        },
    ]


class TestInferencePipeline:
    BASE_URL = "http://host.docker.internal:8000/api/v1/inferencers"
    TIMEOUT = 150  # seconds

    @pytest.fixture(autouse=True)
    def setup(self, model_version):
        """Setup test environment."""
        self.model_version = model_version
        self.model_id = model_version.api_identifier

    def test_pipeline_health(self):
        """Test if the inference pipeline is running."""
        response = requests.get("http://host.docker.internal:8000/health")
        assert response.status_code == 200
        assert response.json().get("status") == "healthy"

    def test_model_loading(self):
        """Test loading the model and checking its status."""
        # Request model loading
        load_response = requests.post(f"{self.BASE_URL}/{self.model_id}/load")
        assert load_response.status_code == 200
        assert load_response.json().get("status") != ModelStatusEnum.FAILED

        # Poll status until loaded or timeout
        start_time = time.time()
        while time.time() - start_time < self.TIMEOUT:
            status_response = requests.get(f"{self.BASE_URL}/{self.model_id}/status")
            assert status_response.status_code == 200

            status = status_response.json().get("status")
            if status == ModelStatusEnum.LOADED:
                break
            elif status in [ModelStatusEnum.FAILED, ModelStatusEnum.UNKNOWN]:
                pytest.fail(f"Model loading failed with status: {status}")

            time.sleep(5)  # Wait before next check
        else:
            pytest.fail("Model loading timed out")

    def test_create_inference_job(self, db, test_data, collection):
        """Test creating and monitoring an inference job."""
        # Create inference job
        inference_job = InferenceJob.objects.create(
            collection=collection, classification_type=ClassificationType.DIVISION, status=InferenceJobStatus.QUEUED
        )

        # Process test data through batch processor
        batch_processor = BatchProcessor(BatchConfig())
        batch = batch_processor.prepare_url_data(test_data[0])  # Test with first item

        # Create external job
        external_job = inference_job.create_external_job([batch])
        assert external_job is not None
        assert external_job.status == ExternalJobStatus.QUEUED

        # Submit data to API
        texts = [item["text"] for item in test_data]
        job_response = requests.post(f"{self.BASE_URL}/{self.model_id}/jobs", json={"input_data": texts})
        assert job_response.status_code == 200
        job_data = job_response.json()
        assert "job_id" in job_data

        # Monitor job status
        job_id = job_data["job_id"]
        start_time = time.time()

        while time.time() - start_time < self.TIMEOUT:
            status_response = requests.get(f"{self.BASE_URL}/{self.model_id}/jobs/{job_id}")
            assert status_response.status_code == 200

            status = status_response.json().get("status")
            if status == "completed":
                results = status_response.json().get("results", [])
                assert len(results) == len(test_data)

                # Verify division labels
                for result in results:
                    assert isinstance(result, dict)
                    assert any(
                        label in result
                        for label in [
                            "Astrophysics",
                            "Earth Science",
                            "Heliophysics",
                            "Planetary Science",
                            "Biological and Physical Sciences",
                        ]
                    )

                # Update external job with results
                external_job.store_results(results)
                external_job.refresh_from_db()
                assert external_job.status == ExternalJobStatus.COMPLETED
                assert external_job.completed_at is not None
                break

            elif status in ["failed", "cancelled", "not_found"]:
                pytest.fail(f"Job failed with status: {status}")

            time.sleep(5)
        else:
            pytest.fail("Job processing timed out")

        # Check inference job completion
        inference_job.refresh_from_db()
        assert inference_job.status == InferenceJobStatus.COMPLETED
        assert inference_job.completed_at is not None

    def test_cleanup(self):
        """Test cleanup by unloading the model."""
        unload_response = requests.post(f"{self.BASE_URL}/{self.model_id}/unload")
        assert unload_response.status_code == 200

        # Verify model is unloaded
        status_response = requests.get(f"{self.BASE_URL}/{self.model_id}/status")
        assert status_response.status_code == 200
        assert status_response.json().get("status") in [ModelStatusEnum.UNLOADED, ModelStatusEnum.UNLOADING]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

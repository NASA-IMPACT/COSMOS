# inference/tests/local_test_inference_api_client.py
# docker-compose -f local.yml run --rm django pytest inference/tests/local_test_inference_api_client.py

"""
This is a test designed to be run on a local machine which has the inference pipeline running
It tests the inference the InferenceAPIClient against a live API
"""

import time

import pytest

from inference.utils.inference_api_client import (
    InferenceAPIClient,
    JobStatusEnum,
    ModelStatusEnum,
)

# Configuration
API_BASE = "http://host.docker.internal:8000"


# Shared client for all tests to use
@pytest.fixture(scope="session")
def client():
    """Provide a configured API client"""
    return InferenceAPIClient(base_url=API_BASE, timeout=10)


# Check API health at the session level and skip all tests if unhealthy
@pytest.fixture(scope="session", autouse=True)
def check_api_health(client):
    """Check if the API is healthy and skip all tests if not"""
    if not client.check_health():
        pytest.skip("API is not healthy, skipping all tests")


# Discover available models and skip all tests if none available
@pytest.fixture(scope="session", autouse=True)
def require_available_model(client):
    """Ensure at least one model is available, or skip all tests"""
    available_models = client.get_available_inferencers()

    # Check if we got a valid response with models
    if (
        isinstance(available_models, dict)
        and not ("status" in available_models and available_models["status"] == JobStatusEnum.FAILED)
        and available_models
    ):
        # Return the available model names for other fixtures to use
        return list(available_models.keys())

    # If no models found, skip all tests
    pytest.skip("No available inference models found, skipping all tests")


# Get a specific model name to use for tests
@pytest.fixture
def model_name(require_available_model):
    """Return the first available model name"""
    return require_available_model[0]


# Ensure clean environment between tests
@pytest.fixture
def clean_environment(client):
    """Ensure no models are loaded before and after tests"""
    client.unload_all_models()
    yield
    client.unload_all_models()


# Model fixture for tests that need a loaded model
@pytest.fixture
def loaded_model(client, clean_environment, model_name):
    """Provide a test with a loaded model"""
    success = client.load_model(model_name)
    assert success, f"Failed to load test model {model_name}"
    return model_name


# Basic API functionality tests
def test_api_connection(client):
    """Test basic API connectivity"""
    response = client.make_api_request("GET", "")
    assert response is not None
    assert response.get("status") != JobStatusEnum.FAILED


def test_make_api_request_error_handling(client):
    """Test the API request error handling"""
    # Test with invalid endpoint
    response = client.make_api_request("GET", "nonexistent-endpoint")
    assert response is not None
    assert response.get("status") == JobStatusEnum.FAILED
    assert "API request failed" in response.get("message", "")


# Model management tests
def test_get_available_models(client, require_available_model):
    """Test retrieval of available models"""
    models = client.get_available_inferencers()

    # If we received an error response
    if isinstance(models, dict) and "status" in models and models["status"] == JobStatusEnum.FAILED:
        pytest.fail("Failed to retrieve available models")

    # Otherwise it should be a dictionary of models
    assert isinstance(models, dict)
    assert models, "Expected at least one model to be available"

    # The first model from our fixture should be in this list
    first_model = require_available_model[0]
    assert first_model in models, f"Previously found model {first_model} not in available models"


def test_model_status_check(client, clean_environment, model_name):
    """Test model status checking"""
    # Initially model should be unloaded, unknown, or failed
    status = client.check_model_status(model_name)
    assert status in [ModelStatusEnum.UNLOADED, ModelStatusEnum.UNKNOWN]


def test_model_load_unload_cycle(client, clean_environment, model_name):
    """Test complete model load/unload cycle"""
    # Start with unloaded model
    initial_status = client.check_model_status(model_name)
    assert initial_status in [ModelStatusEnum.UNLOADED, ModelStatusEnum.UNKNOWN]

    # Load model
    assert client.load_model(model_name) is True
    loaded_status = client.check_model_status(model_name)
    assert loaded_status == ModelStatusEnum.LOADED

    # Unload model
    assert client.unload_all_models() is True
    time.sleep(2)  # Brief wait for unloading to complete
    final_status = client.check_model_status(model_name)
    assert final_status in [ModelStatusEnum.UNLOADED, ModelStatusEnum.UNLOADING]


# Job submission and status tests
def test_batch_submission(client, loaded_model):
    """Test batch job submission and completion"""
    model_name = loaded_model

    # Create simple test batch
    batch_data = [{"text": "Test input 1"}, {"text": "Test input 2"}]

    # Submit batch
    job_id = client.submit_batch(model_name, batch_data)
    assert job_id is not None

    # Wait for job completion (up to 30 seconds)
    for _ in range(15):
        job_status = client.get_job_status(model_name, job_id)
        if job_status.get("status") == JobStatusEnum.COMPLETED:
            results = job_status.get("results")
            assert results is not None
            assert len(results) == len(batch_data)
            return
        elif job_status.get("status") in [JobStatusEnum.FAILED, JobStatusEnum.CANCELLED]:
            pytest.fail(f"Job failed: {job_status.get('message')}")
        time.sleep(2)

    pytest.fail("Job did not complete in expected time")


# Error handling tests
@pytest.mark.parametrize(
    "test_input",
    [
        [],  # Empty batch
        [{"invalid_key": "value"}],  # Invalid structure
    ],
)
def test_invalid_batch_submission(client, model_name, test_input):
    """Test client handles invalid batch data correctly"""
    job_id = client.submit_batch(model_name, test_input)
    assert job_id is None


def test_nonexistent_job_status(client, model_name):
    """Test getting status for nonexistent job"""
    status = client.get_job_status(model_name, "nonexistent-job-id")
    assert status.get("status") in [JobStatusEnum.FAILED, JobStatusEnum.NOT_FOUND]


def test_connection_error_handling():
    """Test handling of connection errors"""
    bad_client = InferenceAPIClient(base_url="http://invalid-host:9999", timeout=1)
    assert bad_client.check_health() is False

    response = bad_client.make_api_request("GET", "")
    assert response.get("status") == JobStatusEnum.FAILED
    assert "API request failed" in response.get("message", "")

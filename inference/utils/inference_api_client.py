# inference/utils/inference_api_client.py
import time
from enum import Enum
from typing import TypedDict, Union

import requests
from django.conf import settings
from tenacity import retry, retry_if_result, stop_after_attempt, wait_fixed

SingleInstaceInput = str
MultiInstanceInput = list[str]
InputData = Union[SingleInstaceInput, MultiInstanceInput]


class JobStatusEnum(str, Enum):
    QUEUED = "queued"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"
    PENDING = "pending"
    CANCELLED = "cancelled"
    NOT_FOUND = "not_found"


class ModelStatusEnum(str, Enum):
    TO_LOAD = "load"
    LOADING = "loading"
    LOADED = "loaded"
    TO_UNLOAD = "unload"
    UNLOADING = "unloading"
    UNLOADED = "unloaded"
    FAILED = "failed"
    UNKNOWN = "unknown"


class APIResponse(TypedDict):
    """Base type for API responses"""

    status: JobStatusEnum | ModelStatusEnum | str
    message: str | None


class JobResponse(APIResponse):
    """Response type for job creation and status"""

    job_id: str
    results: str | list | dict | None


class ModelStatusResponse(APIResponse):
    """Response type for model status"""

    model_identifier: str


class BatchItem(TypedDict):
    """Type for batch inference items"""

    text: str


class InferenceAPIClient:
    """Handles all direct interactions with the Inference API and model management"""

    def __init__(self, base_url: str = settings.INFERENCE_API_URL, timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout

    def check_health(self) -> bool:
        """
        Check if the API is running and healthy.

        Returns:
            bool: True if the API is healthy, False otherwise
        """
        try:
            url = f"{self.base_url}/health"
            response = requests.get(url, timeout=self.timeout)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False

    def make_api_request(self, method: str, endpoint: str, **kwargs) -> JobResponse | ModelStatusResponse | None:
        """Make a request to the inference API with error handling"""
        try:
            url = f"{self.base_url}/api/v1/inferencers/{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            return {"status": JobStatusEnum.FAILED, "message": f"API request failed: {str(e)}"}

    def _request_model_load(self, model_identifier: str) -> bool:
        """Internal method to request model loading from API"""
        response = self.make_api_request("POST", f"{model_identifier}/load")
        return response is not None and response.get("status") != JobStatusEnum.FAILED

    def _request_model_unload(self, model_identifier: str) -> bool:
        """Internal method to request model unloading from API"""
        response = self.make_api_request("POST", f"{model_identifier}/unload")
        return response is not None and response.get("status") != JobStatusEnum.FAILED

    def check_model_status(self, model_identifier: str) -> ModelStatusEnum:
        """Check if model is loaded and ready"""
        response = self.make_api_request("GET", f"{model_identifier}/status")
        if not response:
            return ModelStatusEnum.UNKNOWN

        try:
            return ModelStatusEnum(response.get("status", ModelStatusEnum.UNKNOWN))
        except ValueError:
            return ModelStatusEnum.UNKNOWN

    def submit_batch(self, model_identifier: str, batch_data: list[BatchItem]) -> str | None:
        """Submit a batch of items for inference"""
        if not batch_data:
            return None

        # Validate and extract text data
        try:
            text_data = [item["text"] for item in batch_data]
        except (KeyError, TypeError):
            return None

        response = self.make_api_request("POST", f"{model_identifier}/jobs", json={"input_data": text_data})
        return response.get("job_id") if response else None

    def get_job_status(self, model_identifier: str, job_id: str) -> JobResponse:
        """Check status of a submitted job"""
        response = self.make_api_request("GET", f"{model_identifier}/jobs/{job_id}")
        if not response:
            return {
                "status": JobStatusEnum.FAILED,
                "message": "Failed to get job status",
                "job_id": job_id,
                "results": None,
            }
        return response

    def get_available_inferencers(self) -> dict:
        """Get all available inferencer models"""
        response = self.make_api_request("GET", "")
        return response if response else {}

    def unload_all_models(self) -> bool:
        """Unload all models

        Returns:
            bool: True if all models were successfully unloaded
        """
        try:
            # Get all available models
            available_models = self.get_available_inferencers()

            # Unload all models
            for model_id in available_models:
                status = self.check_model_status(model_id)
                if status == ModelStatusEnum.LOADED:
                    if not self._request_model_unload(model_id):
                        return False
            return True
        except Exception:
            return False

    def wait_for_model_loading(self, model_identifier: str, max_attempts: int = 10, wait_time: int = 5) -> bool:
        """
        Wait for a model to finish loading.

        Args:
            model_identifier: The model to check
            max_attempts: Maximum number of status checks
            wait_time: Seconds to wait between checks

        Returns:
            bool: True if model is loaded, False otherwise
        """
        for _ in range(max_attempts):
            status = self.check_model_status(model_identifier)
            if status == ModelStatusEnum.LOADED:
                return True
            elif status == ModelStatusEnum.FAILED:
                return False
            elif status in [ModelStatusEnum.LOADING, ModelStatusEnum.TO_LOAD]:
                # Model is still loading, wait and try again
                time.sleep(wait_time)
            else:
                # Unexpected status
                return False
        return False  # Timed out without reaching LOADED state

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(30), retry=retry_if_result(lambda x: not x))
    def load_model(self, model_identifier: str) -> bool:
        """
        Load a specific model, first unloading all models, and wait for loading to complete.

        Args:
            model_identifier: The model to load

        Returns:
            bool: True if the model is successfully loaded
        """
        # First unload all models
        if not self.unload_all_models():
            return False

        # Check current status of our model
        status = self.check_model_status(model_identifier)

        # If already loaded, we're done
        if status == ModelStatusEnum.LOADED:
            return True

        # Try loading if in a state where we can load
        if status in [ModelStatusEnum.UNLOADED, ModelStatusEnum.FAILED, ModelStatusEnum.UNKNOWN]:
            load_request_success = self._request_model_load(model_identifier)
            if not load_request_success:
                return False

            # Now wait for loading to complete
            return self.wait_for_model_loading(model_identifier)

        return False

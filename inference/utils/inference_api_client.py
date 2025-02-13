# inference/utils/inference_api_client.py
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
    """Handles all direct interactions with the Inference API"""

    def __init__(self, base_url: str = settings.INFERENCE_API_URL, timeout: int = 120):
        self.base_url = base_url
        self.timeout = timeout

    def make_api_request(self, method: str, endpoint: str, **kwargs) -> JobResponse | ModelStatusResponse | None:
        """Make a request to the inference API with error handling"""
        try:
            url = f"{self.base_url}/api/v1/inferencers/{endpoint}"
            response = requests.request(method, url, timeout=self.timeout, **kwargs)
            response.raise_for_status()
            return response.json() if response.content else None
        except requests.exceptions.RequestException as e:
            return {"status": JobStatusEnum.FAILED, "message": f"API request failed: {str(e)}"}

    def load_model(self, model_identifier: str) -> bool:
        """Request model loading from API"""
        response = self.make_api_request("POST", f"{model_identifier}/load")
        return response is not None and response.get("status") != JobStatusEnum.FAILED

    def unload_model(self, model_identifier: str) -> bool:
        """Request model unloading from API"""
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


class ModelManager:
    """Handles model loading/unloading and ensures only the specified model is loaded"""

    def __init__(self, api_client: InferenceAPIClient, model_identifier: str):
        """Initialize with API client and the model to manage

        Args:
            api_client: InferenceAPIClient instance
            model_identifier: The model this manager will handle
        """
        self.api_client = api_client
        self.model_identifier = model_identifier

    def _unload_all_other_models(self) -> bool:
        """Unload all models except the one managed by this instance"""
        try:
            # Get all available models
            available_models = self.api_client.get_available_inferencers()

            # Unload all models except our target model
            for model_id in available_models:
                if model_id != self.model_identifier:
                    status = self.api_client.check_model_status(model_id)
                    if status == ModelStatusEnum.LOADED:
                        if not self.api_client.unload_model(model_id):
                            return False
            return True
        except Exception:
            return False

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(30), retry=retry_if_result(lambda x: not x))
    def ensure_model_loaded(self) -> bool:
        """Ensure only this model is loaded and ready

        Returns:
            bool: True if the model is successfully loaded and all others unloaded
        """
        # First unload all other models
        if not self._unload_all_other_models():
            # TODO: it might be possible to get stuck in an error state here until we hit the retry limit
            # and then not have logged any errors within the application
            return False

        # Check current status of our model
        status = self.api_client.check_model_status(self.model_identifier)

        # If already loaded, we're done
        if status == ModelStatusEnum.LOADED:
            return True

        # Try loading if in a state where we can load
        if status in [ModelStatusEnum.UNLOADED, ModelStatusEnum.FAILED, ModelStatusEnum.UNKNOWN]:
            return self.api_client.load_model(self.model_identifier)

        return False

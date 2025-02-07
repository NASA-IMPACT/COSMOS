# docker-compose -f local.yml run --rm django pytest -s inference/tests/local_test_inference_integration.py
"""
This is a test designed to be run on a local machine which has the inference pipeline running,
    to ensure that the pipeline is functioning correctly.
It also serves as a guide for how to send requests to the inference pipeline.
"""

import time

import pytest
import requests


class TestInferencePipeline:
    BASE_URL = "http://host.docker.internal:8000/api/v1/inferencers"
    MODEL_ID = "DC"  # Using TDAMM classifier as example
    TIMEOUT = 150  # seconds

    def test_pipeline_health(self):
        """Test if the inference pipeline is running"""
        response = requests.get("http://host.docker.internal:8000/health")
        assert response.status_code == 200

    def test_model_loading(self):
        """Test loading the model and checking its status"""
        # Request model loading
        load_response = requests.post(f"{self.BASE_URL}/{self.MODEL_ID}/load")
        assert load_response.status_code == 200

        # Poll status until loaded or timeout
        start_time = time.time()
        while time.time() - start_time < self.TIMEOUT:
            status_response = requests.get(f"{self.BASE_URL}/{self.MODEL_ID}/status")
            assert status_response.status_code == 200

            status = status_response.json().get("status")
            if status == "loaded":
                break
            elif status in ["failed", "unknown"]:
                pytest.fail(f"Model loading failed with status: {status}")

            time.sleep(5)  # Wait before next check
        else:
            pytest.fail("Model loading timed out")

    def test_create_inference_job(self):
        """Test creating and monitoring an inference job"""
        # Sample data for inference with metadata
        test_data = [
            {
                "url_id": 1,
                "text": "This is a sample text about astrophysics and space exploration.",
                "metadata": {"url": "http://example.com/doc1"},
            },
            {
                "url_id": 2,
                "text": "The sun is a star, and it is the center of our solar system.",
                "metadata": {"url": "http://example.com/doc2"},
            },
            {
                "url_id": 3,
                "text": "The Earth is our home, and it is full of life.",
                "metadata": {"url": "http://example.com/doc3"},
            },
        ]

        # Extract just the texts for the model
        texts = [item["text"] for item in test_data]

        # Create job with just the texts
        job_response = requests.post(f"{self.BASE_URL}/{self.MODEL_ID}/jobs", json={"input_data": texts})
        assert job_response.status_code == 200
        job_data = job_response.json()
        assert "job_id" in job_data

        # Monitor job status
        job_id = job_data["job_id"]
        start_time = time.time()

        while time.time() - start_time < self.TIMEOUT:
            status_response = requests.get(f"{self.BASE_URL}/{self.MODEL_ID}/jobs/{job_id}")
            assert status_response.status_code == 200

            status = status_response.json().get("status")
            if status == "completed":
                # Get results and add back metadata
                results = status_response.json().get("results", [])
                assert len(results) == len(test_data)

                # Each result should be a dictionary of label->score mappings
                for result in results:
                    assert isinstance(result, dict)
                    # Verify some NASA division labels are present
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
                break
            elif status in ["failed", "cancelled", "not_found"]:
                pytest.fail(f"Job failed with status: {status}")

            time.sleep(5)  # Wait before next check
        else:
            pytest.fail("Job processing timed out")

    def test_cleanup(self):
        """Test cleanup by unloading the model"""
        unload_response = requests.post(f"{self.BASE_URL}/{self.MODEL_ID}/unload")
        assert unload_response.status_code == 200

        # Verify model is unloaded
        status_response = requests.get(f"{self.BASE_URL}/{self.MODEL_ID}/status")
        assert status_response.status_code == 200
        assert status_response.json().get("status") in ["unloaded", "unloading"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

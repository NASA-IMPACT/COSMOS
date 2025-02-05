# COSMOS Inference Pipeline

## Overview
COSMOS uses an ML inference pipeline to analyze and classify website content. This pipeline processes full-text content from URLs within collections to enhance metadata with classifications such as TDAMM categories (36 types) or science divisions (5 types).

## Infrastructure
We are running both local and prod in docker compose. On local, we are using celery and redis. On prod, we point to AWS SQS instead.

We can log into flower locally at http://localhost:5555. The user and password can be found inside of .envs/.local/.django.

I'm not sure where prod flower is being ported yet. Need to find out.

## Core Components

### Collections and URLs
- **Collections**: Store website-level metadata
- **DeltaUrl/CuratedUrl**: Store individual URL metadata including full text content

### Classification Process
1. **Initiation**
   - Curator/engineer triggers classification via COSMOS UI
   - Collection is added to processing queue with specified classification type

2. **Scheduled Processing**
   - Processing occurs during off-peak hours (6 PM - 7 AM)
   - Celery Beat scheduler runs two tasks every 5 minutes:
     - `schedule_inference_job`: Manages job scheduling
     - `poll_inference_results`: Checks job status and retrieves results

3. **Job Processing Flow**
   - System checks for available jobs
   - For each job:
     1. Associated model is loaded
     2. URLs with full texts are grouped into API-friendly batches
     3. Batches are sent to inference API
     4. Job IDs are stored for tracking by results polling

4. **Job Results Processing**
   - System checks for running jobs
     1. API checks for job status
     2. If finished, results stored
     3. Job status updated

## Key Functions

### Model Management
```python
def load_model():
    """
    Loads the required classification model
    - Checks model status
    - Returns loading errors
    - Times out after 2.5 minutes of unsuccessful loading
    """

def unload_model():
    """
    Safely unloads models when needed
    - Confirms unload completion
    - Returns unloading errors
    """
```

### Data Processing
```python
def batch_data():
    """
    Creates efficient batches of URL data for processing
    Similar to implementation in sde_collections.sinequa_api
    """

def send_inference_job():
    """
    Manages the inference job submission process:
    1. Unloads other models if necessary
    2. Loads required model
    3. Sends batched data to API
    4. Records external job ID
    """
```

### Job Management
```python
def schedule_inference_job():
    """
    Manages job queue:
    - Checks for currently processing jobs
    - Schedules next available job if queue is clear
    """

def poll_inference_results():
    """
    Monitors and processes job results:
    - Checks status of processing jobs
    - Retrieves completed classifications
    - Updates job status
    """
```

## Architecture Notes

### Classification Type Management
- InferenceJob tracks classification type
- Model selection handled by ClassificationTypes.get_model_identifier()
- Future consideration: Add model tracking for classification provenance
  - Consider creating a model to link classifications with their source models
  - Enable tracking of which model version produced which classifications

## Resources
- [Inference Pipeline Example Usage](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline?tab=readme-ov-file#example-usage)
- [Inference Pipeline API Documentation](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline/blob/develop/API.md)
- [Inference Pipeline Doc](https://docs.google.com/document/d/1KapWcHZdHw91h_bs8Nx3XtZ5Puhc3IYJNDYle89NEP4/edit?tab=t.15jmko27foev#heading=h.1620ajmrp24g)

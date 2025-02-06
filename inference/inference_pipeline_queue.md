# COSMOS Inference Pipeline

## Overview
COSMOS uses an ML inference pipeline to analyze and classify website content. This pipeline processes full-text content from URLs within collections to enhance metadata with classifications such as TDAMM categories (36 types) or science divisions (5 types).

## Infrastructure
We are running both local and prod in docker compose. On local, we are using celery and redis. On prod, we point to AWS SQS instead.

We can log into flower locally at http://localhost:5555. The user and password can be found inside of .envs/.local/.django.

## Core Components

### Collections and URLs
- **Collections**: Store website-level metadata
- **DeltaUrl/CuratedUrl**: Store individual URL metadata including full text content and paired field descriptors

### Job Structure
The inference pipeline uses a two-level job system:

1. **InferenceJob**
   - Created for each collection that needs processing
   - Tracks overall progress and classification type
   - Contains multiple ExternalJobs
   - Manages cleanup of completed jobs

2. **ExternalJob**
   - Created for each batch of URLs from a collection
   - Tracks specific inference API job status and results
   - Links back to parent InferenceJob
   - Stores API job IDs for result retrieval

### Classification Process
1. **Initiation**
   - Curator/engineer triggers classification via COSMOS UI
   - Collection is added to processing queue with specified classification type
   - InferenceJob is created for the collection

2. **Batch Processing**
   - Collection URLs are divided into batches
   - Each batch creates an ExternalJob
   - ExternalJobs are sent to inference API
   - Job IDs and status are tracked

3. **Results Processing**
   - System polls inference API for ExternalJob status
   - When a batch completes:
     1. Results are retrieved from API
     2. Database is updated using PairedFieldDescriptor
     3. ExternalJob is marked complete
   - When all ExternalJobs complete:
     1. InferenceJob is marked complete
     2. Cleanup process removes ExternalJobs

4. **Data Storage**
   - Results are stored using PairedFieldDescriptor system
   - For example, TDAMM classifications update `deltaurl.tdamm_tag_ml`
   - Manual entries (`_manual`) take precedence over ML results (`_ml`)

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

### Job Management
```python
def create_inference_job(collection, classification_type):
    """
    Creates main InferenceJob for a collection:
    - Validates collection status
    - Sets up job tracking
    - Initializes external job creation
    """

def create_external_jobs(inference_job):
    """
    Creates batch-level ExternalJobs:
    - Batches collection URLs
    - Creates API jobs
    - Links jobs to parent InferenceJob
    """

def cleanup_completed_job(inference_job):
    """
    Performs cleanup after job completion:
    - Verifies all ExternalJobs are complete
    - Updates final statuses
    - Removes ExternalJob records
    """
```

### Data Processing
```python
def process_batch_results(external_job):
    """
    Handles completed batch results:
    1. Retrieves results from API
    2. Updates database using PairedFieldDescriptor
    3. Marks ExternalJob as complete
    """

def update_ml_fields(urls, results):
    """
    Updates ML fields in database:
    - Maps API results to correct URLs
    - Uses PairedFieldDescriptor to update _ml fields
    - Preserves existing manual entries
    """
```


## Architecture Notes

### Classification Type Management
- InferenceJob tracks classification type
- Model selection handled by ClassificationTypes.get_model_identifier()
- Future consideration: Add model tracking for classification provenance
  - Consider creating a model to link classifications with their source models
  - Enable tracking of which model version produced which classifications

### Data Storage Patterns
- Uses PairedFieldDescriptor for all ML-enhanced fields
- Maintains separation between manual and ML data
- Enables easy comparison and override of ML results
- Supports automated updates without affecting manual entries

## Resources
- [Inference Pipeline Example Usage](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline?tab=readme-ov-file#example-usage)
- [Inference Pipeline API Documentation](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline/blob/develop/API.md)
- [Inference Pipeline Doc](https://docs.google.com/document/d/1KapWcHZdHw91h_bs8Nx3XtZ5Puhc3IYJNDYle89NEP4/edit?tab=t.15jmko27foev#heading=h.1620ajmrp24g)

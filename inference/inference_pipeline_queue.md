# COSMOS Inference Pipeline

## Overview
COSMOS uses an ML inference pipeline to analyze and classify website content. This pipeline processes full-text content from URLs within collections to enhance metadata with classifications such as TDAMM categories (36 types) or science divisions (5 types).

## Infrastructure
We are running both local and prod in docker compose. On local, we are using celery and redis. On prod, we point to AWS SQS instead.

We can log into flower locally at http://localhost:5555. The user and password can be found inside of .envs/.local/.django.

## Core Components

### Collections and URLs
- **Collections**: Store website-level metadata
- **DeltaUrl/CuratedUrl**: Store individual URL metadata including full text content and paired field descriptors which will hold classification results

### Job Structure
The inference pipeline uses a two-level job system:

1. **InferenceJob**
   - Created for each collection that needs processing
   - Links to a Collection
   - Tracks classification type
   - References multiple ExternalJobs
   - Tracks overall progress of children ExternalJobs
   - Manages cleanup of completed jobs

2. **ExternalJob**
   - Created for each batch of URLs from a collection
   - Links to a parent InferenceJob
   - Links to a specific API job_id
   - Tracks job_id's: status, results, and error

### Classification Process
1. **def generate_inference_job(collection, classification_type)**
   - Curator/engineer triggers classification via COSMOS UI
   - InferenceJob is created for the collection/classification pair

2. **Chron**
   - Every 5 minutes, between 6pm-7am, attempts to process_inference_job_queue()
     - this could either mean batching and api sending
     - or it could mean reading in results from an open InferenceJob

3. **def process_inference_job_queue()**
   - Loop through all InferenceJob objects to find status=Pending
     - If none, find an InferenceJob.status=Queued and initiate_inference_job()
     - If exists, for all InferenceJob.ExternalJobs.status=Pending, process_external_job()
     - Evaluate if InferenceJob is complete

4. **def initiate_inference_job(inference_job)**
   - load_model()
   - Batch urls
   - For each batch:
     - Generate ExternalJob

5. **def batch_urls(collection?)**
   - iterator?
   - returns ([url_list], [full_text_list])
   - batches should be based on sum(len(full_text)), not count(url)

6. **def generate_external_job(batch, classification_type)**
   - send full texts to API and recieve job_id
   - create ExternalJob with all metadata

7. **def process_external_job**
   - Ping API with the current ExternalJob.job_id
   - Record status
   - Optionally record results or error

8. **def evaluate_inference_job**
   - Can be InProgress, Completed, or Failed
   - If All ExternalJobs.status=Completed
    - InferenceJob.status=Completed
   - If any ExternalJob.status=PENDING
    - InferenceJob.status=InProgress
   - If no ExternalJobs.status=PENDING and any ExternalJobs.status=FAILED,UNKNOWN,NOT_FOUND,CANCELLED
    - InferenceJob.status=Failed

9. **def cleanup_inference_job**
   - unload_model()

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


## Resources
- [Inference Pipeline Example Usage](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline?tab=readme-ov-file#example-usage)
- [Inference Pipeline API Documentation](https://github.com/NASA-IMPACT/llm-app-classifier-pipeline/blob/develop/API.md)
- [Inference Pipeline Doc](https://docs.google.com/document/d/1KapWcHZdHw91h_bs8Nx3XtZ5Puhc3IYJNDYle89NEP4/edit?tab=t.15jmko27foev#heading=h.1620ajmrp24g)


## Todo
- database saving and job sending should be handled at a batch level, so that we can retry batches which failed, without needing to re-run the entire collection
- database should not allow the creation of a a second InferenceJob if an existing Job exists where InferenceJob(collection=collection,classification_type=classification_type,completed=False)
- Long-term:Enable tracking of which model version produced which classifications. this should be stored at the level of the paired field

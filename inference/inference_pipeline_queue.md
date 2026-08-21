# COSMOS Inference Pipeline

> **DORMANT — the inference pipeline is disabled, not deleted.**
> As of Phase 2 the entire pipeline is gated on the `INFERENCE_ENABLED` setting
> (`config/settings/base.py`), which defaults to `False`. While the flag is off:
> - `Collection.queue_necessary_classifications()` never creates an `InferenceJob`; it
>   goes straight to `migrate_dump_to_delta_and_handle_status_transistions`.
> - `process_inference_job_queue()` returns immediately without touching the queue.
> - The two `PeriodicTask` beat rows created in `inference/signals.py` are written with
>   `enabled=settings.INFERENCE_ENABLED`, so beat never fires them.
>
> The models, tasks, and API client all remain in the tree. Everything below describes
> how the pipeline behaves **when `INFERENCE_ENABLED` is turned back on**.

## Overview
The server runs both the COSMOS curation app and an ML Inference Pipeline, which can analyze and classify website content. When enabled, COSMOS processes whole collections and sends the full_texts of the individual urls to the Inference Pipeline for classification. Right now it supports Division Classifications and TDAMM Classifications.

The Inference Pipeline can support multiple model versions for a single classification type. When a collection needs to be classified for certain classification and model, say "Division" and "v1", the COSMOS app will create an InferenceJob object. The InferenceJob will then create ExternalJob objects for each batch of urls in the collection. The ExternalJob objects will send the full_texts to the Inference Pipeline API, which will return a job_id. The ExternalJob will then ping the API with the job_id to get the results. Once all ExternalJobs are complete, the InferenceJob will be marked as complete.

## Infrastructure
We are running both local and prod in docker compose. On local, we are using celery and redis. On prod, we point to AWS SQS instead.

We can log into flower locally at http://localhost:5555. The user and password can be found inside of .envs/.local/.django.

## Core Components

### Collections and URLs
- **Collection**: Stores website-level metadata
- **DeltaUrl/CuratedUrl**: Stores individual URL metadata including full text content and paired field descriptors which will hold classification results

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
   - When enabled, every 5 minutes between 6pm-7am, attempts to process_inference_job_queue()
     - this could either mean batching and api sending
     - or it could mean reading in results from an open InferenceJob
   - The beat rows are created disabled while `INFERENCE_ENABLED` is `False`, and
     `process_inference_job_queue()` itself short-circuits on the same flag, so a
     hand-enabled row or an ad-hoc invocation still processes nothing

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

## Documentation Todo
- write about ModelVersion, and how we have active versions. Explain the api_identifier, etc

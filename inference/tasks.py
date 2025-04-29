# inference/tasks.py
from celery import shared_task

from inference.models import InferenceJob, InferenceJobStatus
from inference.utils.advisory_lock import AdvisoryLock


@shared_task
def process_inference_job_queue():
    """
    Main job queue processor that runs every 5 minutes between 6pm-7am.
    Uses Postgres advisory locking to ensure only one instance runs at a time.
    """
    lock = AdvisoryLock("inference_queue_lock")

    with lock.hold() as acquired:
        if not acquired:
            return "Queue processing already in progress"

        try:
            # Look for pending jobs first
            pending_jobs = InferenceJob.objects.filter(status=InferenceJobStatus.PENDING)

            if pending_jobs.exists():
                # Refresh and process pending jobs
                for job in pending_jobs:
                    job.refresh_external_jobs_status_and_store_results()
                    job.reevaluate_progress_and_update_status()
            else:
                # If no pending jobs, try to initiate a queued job
                queued_job = (
                    InferenceJob.objects.filter(status=InferenceJobStatus.QUEUED).order_by("created_at").first()
                )

                if queued_job:
                    queued_job.initiate()

            return "Queue processing completed successfully"

        except Exception as e:
            return f"Error processing queue: {str(e)}"

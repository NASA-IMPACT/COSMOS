# config/celery.py
import os

from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("cosmos")

# Configure Celery using Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "process-inference-queue": {
        "task": "inference.tasks.process_inference_job_queue",
        # Only run between 6pm and 7am
        "schedule": crontab(minute="*/5", hour="18-23,0-6"),
    },
}

# config/celery.py
import os

from celery import Celery

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("cosmos")

# Configure Celery using Django settings
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs
app.autodiscover_tasks()

"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="BoLug3vIqSX5NQEuAC7DiD5jfdvEo0PYolwms2pw3mUv7nBOc10PpSGU8GnrpSv8",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore # noqa F405

# CELERY
# ------------------------------------------------------------------------------
# Never publish to the real broker from tests. The container entrypoint exports
# CELERY_BROKER_URL=${REDIS_URL} — the same Redis the celeryworker container consumes —
# so any test that changes a workflow status without patching .delay() would enqueue a
# real message, and the live worker would run it against the LOCAL database (test-DB
# collection ids can collide with local rows, flipping their statuses). kombu's
# memory:// transport queues in-process and dies with the test run.
# Celery gives the CELERY_BROKER_URL *environment variable* precedence over Django
# settings, so the env var must be overridden too; this runs at settings import, before
# the celery app's lazy config finalizes.
import os  # noqa: E402

os.environ["CELERY_BROKER_URL"] = "memory://"
CELERY_BROKER_URL = "memory://"
# Your stuff...
# ------------------------------------------------------------------------------

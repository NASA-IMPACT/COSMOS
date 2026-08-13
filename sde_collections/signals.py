from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

POLL_SCRAPE_TASK = "sde_collections.tasks.poll_scrape_jobs"
POLL_SCRAPE_TASK_NAME = "Poll crawler S3 results (every 5 min)"


@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    """DB-row beat schedule for the scrape-results poller (there is no
    CELERY_BEAT_SCHEDULE in this repo — all schedules are django-celery-beat rows).

    `enabled` is re-asserted from SCRAPE_POLL_ENABLED on every migrate, same pattern as
    inference/signals.py: the flag, not a hand-edit in the admin, is the source of truth.
    """
    if sender.name != "sde_collections":
        return

    from django_celery_beat.models import CrontabSchedule, PeriodicTask

    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute="*/5",
        hour="*",
        day_of_week="*",
        day_of_month="*",
        month_of_year="*",
    )

    try:
        task = PeriodicTask.objects.get(name=POLL_SCRAPE_TASK_NAME)
    except PeriodicTask.DoesNotExist:
        PeriodicTask.objects.create(
            crontab=crontab,
            name=POLL_SCRAPE_TASK_NAME,
            task=POLL_SCRAPE_TASK,
            enabled=settings.SCRAPE_POLL_ENABLED,
        )
    else:
        task.crontab = crontab
        task.task = POLL_SCRAPE_TASK
        task.enabled = settings.SCRAPE_POLL_ENABLED
        task.save()

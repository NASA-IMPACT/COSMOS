from django.conf import settings
from django.db.models.signals import post_migrate
from django.dispatch import receiver

POLL_SCRAPE_TASK = "sde_collections.tasks.poll_scrape_jobs"
POLL_SCRAPE_TASK_NAME = "Poll crawler S3 results (every 5 min)"
POLL_INDEX_TASK = "sde_collections.tasks.poll_index_runs"
POLL_INDEX_TASK_NAME = "Poll index runs (every 2 min)"


def _ensure_beat_row(name, task_path, crontab, enabled):
    from django_celery_beat.models import PeriodicTask

    try:
        task = PeriodicTask.objects.get(name=name)
    except PeriodicTask.DoesNotExist:
        PeriodicTask.objects.create(crontab=crontab, name=name, task=task_path, enabled=enabled)
    else:
        task.crontab = crontab
        task.task = task_path
        task.enabled = enabled
        task.save()


@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    """DB-row beat schedules for the S3 pollers (there is no CELERY_BEAT_SCHEDULE in
    this repo — all schedules are django-celery-beat rows).

    `enabled` is re-asserted from the flags on every migrate, same pattern as
    inference/signals.py: the flag, not a hand-edit in the admin, is the source of truth.
    """
    if sender.name != "sde_collections":
        return

    from django_celery_beat.models import CrontabSchedule

    def crontab_every(minutes):
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=f"*/{minutes}",
            hour="*",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )
        return crontab

    _ensure_beat_row(
        POLL_SCRAPE_TASK_NAME, POLL_SCRAPE_TASK, crontab_every(5), settings.SCRAPE_POLL_ENABLED
    )
    _ensure_beat_row(
        POLL_INDEX_TASK_NAME, POLL_INDEX_TASK, crontab_every(2), settings.INDEX_POLL_ENABLED
    )

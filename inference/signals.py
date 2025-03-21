from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    if sender.name == "inference":
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        # Create schedule for every 5 minutes between 6pm-7am
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            hour="18-23,0-6",
            day_of_week="*",
            day_of_month="*",
            month_of_year="*",
        )

        # Create the periodic task if it doesn't exist
        PeriodicTask.objects.get_or_create(
            crontab=crontab,
            name="Process inference queue (6pm-7am)",
            task="inference.tasks.process_inference_job_queue",
        )

        # Create schedule the weekend
        weekend_crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            hour="*",
            day_of_week="0,6",
            day_of_month="*",
            month_of_year="*",
        )

        # Create the periodic task if it doesn't exist
        PeriodicTask.objects.get_or_create(
            crontab=weekend_crontab,
            name="Process inference queue (Weekends)",
            task="inference.tasks.process_inference_job_queue",
        )

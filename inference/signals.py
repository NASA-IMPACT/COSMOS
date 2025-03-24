from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def create_periodic_tasks(sender, **kwargs):
    if sender.name == "inference":
        from django_celery_beat.models import CrontabSchedule, PeriodicTask

        # Weekday evening schedule (6pm-7am)
        weekday_crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            hour="18-23,0-6",
            day_of_week="1-5",  # Monday-Friday
            day_of_month="*",
            month_of_year="*",
        )

        # Weekend schedule (all day)
        weekend_crontab, _ = CrontabSchedule.objects.get_or_create(
            minute="*/5",
            hour="*",
            day_of_week="0,6",  # Saturday-Sunday
            day_of_month="*",
            month_of_year="*",
        )

        # Check if weekday task exists
        weekday_task_name = "Process inference queue (6pm-7am)"
        weekday_task_exists = PeriodicTask.objects.filter(name=weekday_task_name).exists()

        if not weekday_task_exists:
            PeriodicTask.objects.create(
                crontab=weekday_crontab,
                name=weekday_task_name,
                task="inference.tasks.process_inference_job_queue",
            )
        else:
            weekday_task = PeriodicTask.objects.get(name=weekday_task_name)
            weekday_task.crontab = weekday_crontab
            weekday_task.task = "inference.tasks.process_inference_job_queue"
            weekday_task.save()

        # Check if weekend task exists
        weekend_task_name = "Process inference queue (Weekends)"
        weekend_task_exists = PeriodicTask.objects.filter(name=weekend_task_name).exists()

        if not weekend_task_exists:
            PeriodicTask.objects.create(
                crontab=weekend_crontab,
                name=weekend_task_name,
                task="inference.tasks.process_inference_job_queue",
            )
        else:
            weekend_task = PeriodicTask.objects.get(name=weekend_task_name)
            weekend_task.crontab = weekend_crontab
            weekend_task.task = "inference.tasks.process_inference_job_queue"
            weekend_task.save()

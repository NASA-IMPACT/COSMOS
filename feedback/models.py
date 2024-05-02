from django.db import models
from django.utils import timezone

from sde_collections.utils.slack_utils import send_slack_message


class Feedback(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=400)
    comments = models.TextField()
    source = models.CharField(max_length=50, default="SDE", blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Feedback Response"
        verbose_name_plural = "Feedback Responses"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        is_new = self._state.adding
        if is_new:
            message = self.format_notification_message()
            try:
                send_slack_message(message)
            except Exception as e:
                print(f"Failed to send slack message: {e}")
        super().save(*args, **kwargs)

    def format_notification_message(self):
        """
        Returns a formatted notification message containing details from this Feedback instance.
        """
        notification_message = (
            f"<!here> Hey team!! Good news! We've received a new feedback! :rocket: Here are the details : \n"
            f"Name: {self.name}\n"
            f"Email: {self.email}\n"
            f"Subject: {self.subject}\n"
            f"Comments: {self.comments}\n"
            f"Source: {self.source}\n"
            f"Received on: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        return notification_message


class ContentCurationRequest(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    scientific_focus = models.CharField(max_length=200)
    data_type = models.CharField(max_length=100)
    data_link = models.CharField(max_length=1000)
    additional_info = models.TextField(default="", blank=True)
    created_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Content Curation Request"
        verbose_name_plural = "Content Curation Requests"

    def save(self, *args, **kwargs):
        if not self.id:
            self.created_at = timezone.now()
        super().save(*args, **kwargs)

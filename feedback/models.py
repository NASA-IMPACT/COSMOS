from django.db import models
from django.utils import timezone

from sde_collections.utils.slack_utils import send_slack_message


class FeedbackFormDropdown(models.Model):
    DEFAULT_OPTIONS = [
        {"name": "I need help or have a general question", "display_order": 1},
        {"name": "I have a data/content question or comment", "display_order": 2},
        {"name": "I would like to report an error", "display_order": 3},
        {"name": "I have an idea or suggested improvement to share", "display_order": 4},
        {"name": "General comment or feedback", "display_order": 5},
    ]

    name = models.CharField(max_length=200)
    display_order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["display_order", "name"]
        verbose_name = "Dropdowm Option"
        verbose_name_plural = "Dropdown Options"

    def __str__(self):
        return self.name


class Feedback(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=400)
    comments = models.TextField()
    source = models.CharField(max_length=50, default="SDE", blank=True)
    dropdown_option = models.ForeignKey(
        FeedbackFormDropdown, on_delete=models.SET_NULL, null=True, related_name="feedback"
    )
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
        dropdown_option_text = self.dropdown_option.name if self.dropdown_option else "No Option Selected"
        notification_message = (
            f"<!here> New Feedback Received : \n"  # noqa: E203
            f"Name: {self.name}\n"
            f"Email: {self.email}\n"
            f"Dropdown Choice: {dropdown_option_text}\n"
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

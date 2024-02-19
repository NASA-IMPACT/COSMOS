from django.db import models
from django.utils import timezone


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
        super().save(*args, **kwargs)


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

from django.db import models


class Feedback(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=400)
    comments = models.TextField()
    source = models.CharField(max_length=50, default="SDE", blank=True)

    class Meta:
        verbose_name = "Feedback Response"
        verbose_name_plural = "Feedback Responses"


class ContentCurationRequest(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    scientific_focus = models.CharField(max_length=200)
    data_type = models.CharField(max_length=100)
    data_link = models.CharField(max_length=1000)
    additional_info = models.TextField(default="", blank=True)

    class Meta:
        verbose_name = "Content Curation Request"
        verbose_name_plural = "Content Curation Requests"

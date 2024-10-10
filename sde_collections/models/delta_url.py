from django.db import models

from .url import Url


class DeltaUrl(Url):
    """Model for storing delta URLs for curation purposes"""

    delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Delta URL"
        verbose_name_plural = "Delta URLs"

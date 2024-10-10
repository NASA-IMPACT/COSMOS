import os
from urllib.parse import urlparse

from django.db import models

from .collection import Collection
from .collection_choice_fields import Divisions, DocumentTypes
from .pattern import ExcludePattern


class UrlQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        return self.annotate(
            excluded=models.Exists(
                ExcludePattern.candidate_urls.through.objects.filter(candidateurl=models.OuterRef("pk"))
            )
        )


class UrlManager(models.Manager):
    def get_queryset(self):
        return UrlQuerySet(self.model, using=self._db).with_exclusion_status()


class Url(models.Model):
    """This is the base URL model which serves as a base for DeltaUrl and CuratedUrl."""

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="urls")
    url = models.CharField("URL", max_length=4096)
    scraped_title = models.CharField(
        "Scraped Title",
        max_length=1024,
        default="",
        blank=True,
        help_text="This is the original title scraped by Sinequa",
    )
    generated_title = models.CharField(
        "Generated Title",
        max_length=1024,
        default="",
        blank=True,
        help_text="This is the title generated based on a Title Pattern",
    )
    visited = models.BooleanField(default=False)
    document_type = models.IntegerField(choices=DocumentTypes.choices, null=True)
    division = models.IntegerField(choices=Divisions.choices, null=True)

    objects = UrlManager()

    class Meta:
        verbose_name = "URL"
        verbose_name_plural = "URLs"
        ordering = ["url"]

    @property
    def fileext(self) -> str:
        parsed_url = urlparse(self.url)
        path = parsed_url.path
        if path.endswith("/") or not path:
            return "html"
        extension = os.path.splitext(path)[1]
        return extension[1:] if extension.startswith(".") else extension or "html"

    def splits(self) -> list[tuple[str, str]]:
        parts = []
        part_string = ""
        for part in self.path.split("/"):
            if part:
                part_string += f"/{part}"
                parts.append((part_string, part))
        return parts

    @property
    def path(self) -> str:
        parsed = urlparse(self.url)
        path = f"{parsed.path}"
        if parsed.query:
            path += f"?{parsed.query}"
        return path

    def __str__(self) -> str:
        return self.url

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

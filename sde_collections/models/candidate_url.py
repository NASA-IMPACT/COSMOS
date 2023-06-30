from urllib.parse import urlparse

from django.db import models

from .collection import Collection
from .collection_choice_fields import DocumentTypes
from .pattern import ExcludePattern


class CandidateURLQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        return self.annotate(
            excluded=models.Exists(
                ExcludePattern.candidate_urls.through.objects.filter(
                    candidateurl=models.OuterRef("pk")
                )
            )
        )


class CandidateURLManager(models.Manager):
    def get_queryset(self):
        return CandidateURLQuerySet(self.model, using=self._db).with_exclusion_status()


class CandidateURL(models.Model):
    """A candidate URL scraped for a given collection."""

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="candidate_urls"
    )
    url = models.CharField("URL")
    scraped_title = models.CharField(
        "Scraped Title",
        default="",
        blank=True,
        help_text="This is the original title scraped by Sinequa",
    )
    generated_title = models.CharField(
        "Generated Title",
        default="",
        blank=True,
        help_text="This is the title generated based on a Title Pattern",
    )
    level = models.IntegerField(
        "Level", default=0, blank=True, help_text="Level in the tree. Based on /."
    )
    visited = models.BooleanField(default=False)
    objects = CandidateURLManager()
    document_type = models.IntegerField(choices=DocumentTypes.choices, null=True)

    class Meta:
        """Meta definition for Candidate URL."""

        verbose_name = "Candidate URL"
        verbose_name_plural = "Candidate URLs"
        ordering = ["url"]
        unique_together = ("collection", "url")

    def splits(self) -> list[tuple[str, str]]:
        """Split the path into multiple collections."""
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

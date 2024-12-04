import os
from urllib.parse import urlparse

from django.db import models

from .collection_choice_fields import Divisions, DocumentTypes
from .delta_patterns import DeltaExcludePattern, DeltaIncludePattern


class DeltaUrlQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        """
        Annotate queryset with exclusion status, taking into account both exclude and include patterns.
        Include patterns take precedence over exclude patterns.
        """
        return self.annotate(
            has_exclude=models.Exists(
                DeltaExcludePattern.delta_urls.through.objects.filter(deltaurl=models.OuterRef("pk"))
            ),
            has_include=models.Exists(
                DeltaIncludePattern.delta_urls.through.objects.filter(deltaurl=models.OuterRef("pk"))
            ),
            excluded=models.Case(
                # If has_include is True, URL is not excluded regardless of exclude patterns
                models.When(has_include=True, then=models.Value(False)),
                # Otherwise, excluded status is determined by presence of exclude pattern
                default=models.F("has_exclude"),
                output_field=models.BooleanField(),
            ),
        )


class CuratedUrlQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        """
        Annotate queryset with exclusion status, taking into account both exclude and include patterns.
        Include patterns take precedence over exclude patterns.
        """
        return self.annotate(
            has_exclude=models.Exists(
                DeltaExcludePattern.curated_urls.through.objects.filter(curatedurl=models.OuterRef("pk"))
            ),
            has_include=models.Exists(
                DeltaIncludePattern.curated_urls.through.objects.filter(curatedurl=models.OuterRef("pk"))
            ),
            excluded=models.Case(
                # If has_include is True, URL is not excluded regardless of exclude patterns
                models.When(has_include=True, then=models.Value(False)),
                # Otherwise, excluded status is determined by presence of exclude pattern
                default=models.F("has_exclude"),
                output_field=models.BooleanField(),
            ),
        )


# Manager classes remain unchanged since they just use the updated QuerySets
class DeltaUrlManager(models.Manager):
    def get_queryset(self):
        return DeltaUrlQuerySet(self.model, using=self._db).with_exclusion_status()


class CuratedUrlManager(models.Manager):
    def get_queryset(self):
        return CuratedUrlQuerySet(self.model, using=self._db).with_exclusion_status()


class BaseUrl(models.Model):
    """Abstract base class for Urls with shared fields and methods."""

    url = models.CharField("Url", unique=True)
    scraped_title = models.CharField(
        "Scraped Title",
        default="",
        blank=True,
        help_text="This is the original title scraped by Sinequa",
    )
    scraped_text = models.TextField(
        "Scraped Text",
        default="",
        blank=True,
        help_text="This is the text scraped by Sinequa",
    )
    generated_title = models.CharField(
        "Generated Title",
        default="",
        blank=True,
        help_text="This is the title generated based on a Title Pattern",
    )

    visited = models.BooleanField(default=False)
    document_type = models.IntegerField(choices=DocumentTypes.choices, null=True)
    division = models.IntegerField(choices=Divisions.choices, null=True)

    class Meta:
        abstract = True
        ordering = ["url"]

    @property
    def fileext(self) -> str:
        # Parse the URL to get the path
        parsed_url = urlparse(self.url)
        path = parsed_url.path

        # Check for cases where the path ends with a slash or is empty, implying a directory or default file
        if path.endswith("/") or not path:
            return "html"

        # Extract the extension from the path
        extension = os.path.splitext(path)[1]

        # Default to .html if no extension is found
        if not extension:
            return "html"

        if extension.startswith("."):
            return extension[1:]
        return extension

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

    def __str__(self):
        return self.url


class DumpUrl(BaseUrl):
    """Stores the raw dump from the server before deltas are calculated."""

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="dump_urls")

    class Meta:
        verbose_name = "Dump Urls"
        verbose_name_plural = "Dump Urls"
        ordering = ["url"]


class DeltaUrl(BaseUrl):
    """Urls that are being curated. Only deltas are stored in this model."""

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="delta_urls")

    objects = DeltaUrlManager()
    to_delete = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Delta Urls"
        verbose_name_plural = "Delta Urls"
        ordering = ["url"]


class CuratedUrl(BaseUrl):
    """Urls that are curated and ready for production"""

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="curated_urls")

    objects = CuratedUrlManager()

    class Meta:
        verbose_name = "Curated Urls"
        verbose_name_plural = "Curated Urls"
        ordering = ["url"]

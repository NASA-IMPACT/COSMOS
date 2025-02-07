import os
from urllib.parse import urlparse

from django.contrib.postgres.fields import ArrayField
from django.db import models

from ..utils.paired_field_descriptor import PairedFieldDescriptor
from .collection_choice_fields import Divisions, DocumentTypes, TDAMMTags
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

    tdamm_tag = PairedFieldDescriptor(
        field_name="tdamm_tag",
        field_type=ArrayField(models.CharField(max_length=255, choices=TDAMMTags.choices), blank=True, null=True),
        verbose_name="TDAMM Tags",
    )

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

    def get_tag_source(self):
        """Returns the source of the TDAMM tags: 'manual', 'ml', or 'Not Set'"""
        # Convert None to empty list for comparison
        manual_tags = self.tdamm_tag_manual or []
        ml_tags = self.tdamm_tag_ml or []

        if manual_tags and manual_tags != []:
            return "manual"
        elif ml_tags and ml_tags != []:
            return "ml"

        return "Not Set"

    def _fields_match(self, other):
        """Compare fields between two URL objects."""
        fields_to_compare = [
            "scraped_title",
            "scraped_text",
            "generated_title",
            "visited",
            "document_type",
            "division",
            "tdamm_tag_manual",
            "tdamm_tag_ml",
        ]
        return all(getattr(self, field) == getattr(other, field) for field in fields_to_compare)

    def add_tag(self, tag: str, source: str) -> None:
        """Add a tag and handle cleanup if needed."""
        if source == "ml":
            current_tags = self.tdamm_tag_ml or []
            new_tags = list(current_tags)
            if tag not in new_tags:
                new_tags.append(tag)
            self.tdamm_tag_manual = new_tags
        else:
            current_tags = self.tdamm_tag_manual or []
            if tag not in current_tags:
                current_tags.append(tag)
                self.tdamm_tag_manual = current_tags

        self.save()
        self._cleanup_if_needed()

    def remove_tag(self, tag: str, source: str) -> None:
        """Remove a tag and handle cleanup if needed."""
        if source == "ml":
            ml_tags = self.tdamm_tag_ml
            if ml_tags:
                new_manual_tags = [t for t in ml_tags if t != tag]
                self.tdamm_tag_manual = new_manual_tags
        else:
            if self.tdamm_tag_manual:
                manual_tags = self.tdamm_tag_manual
                if tag in manual_tags:
                    manual_tags.remove(tag)
                    self.tdamm_tag_manual = manual_tags

        self.save()
        self._cleanup_if_needed()

    def _cleanup_if_needed(self):
        """Override in DeltaUrl to implement cleanup logic."""
        pass

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

    def _cleanup_if_needed(self):
        """Delete if identical to curated URL and not marked for deletion."""
        try:
            curated_url = CuratedUrl.objects.get(collection=self.collection, url=self.url)
            if not self.to_delete and self._fields_match(curated_url):
                self.delete()
        except CuratedUrl.DoesNotExist:
            pass

    class Meta:
        verbose_name = "Delta Urls"
        verbose_name_plural = "Delta Urls"
        ordering = ["url"]


class CuratedUrl(BaseUrl):
    """Urls that are curated and ready for production"""

    collection = models.ForeignKey("Collection", on_delete=models.CASCADE, related_name="curated_urls")
    objects = CuratedUrlManager()

    def _is_delta_identical(self, delta_url):
        """Check if DeltaUrl has identical metadata to CuratedUrl."""
        fields_to_compare = [
            "scraped_title",
            "scraped_text",
            "generated_title",
            "visited",
            "document_type",
            "division",
            "tdamm_tag_manual",
            "tdamm_tag_ml",
        ]
        return all(getattr(delta_url, field) == getattr(self, field) for field in fields_to_compare)

    def _create_or_update_delta(self):
        """Create or update delta URL using collection's delta migration logic."""
        self.collection.create_or_update_delta_url(self, to_delete=False)
        return self.collection.delta_urls.get(url=self.url)

    def add_tag(self, tag: str, source: str) -> None:
        """Create/update DeltaUrl and add tag to it."""
        delta_url = self._create_or_update_delta()
        if delta_url:
            delta_url.add_tag(tag, source)
            if not delta_url.to_delete and delta_url.tdamm_tag == self.tdamm_tag:
                delta_url.delete()

    def remove_tag(self, tag: str, source: str) -> None:
        """Create/update DeltaUrl and remove tag from it."""
        delta_url = self._create_or_update_delta()
        if delta_url:
            delta_url.remove_tag(tag, source)
            if not delta_url.to_delete and delta_url.tdamm_tag == self.tdamm_tag:
                delta_url.delete()

    class Meta:
        verbose_name = "Curated Urls"
        verbose_name_plural = "Curated Urls"
        ordering = ["url"]

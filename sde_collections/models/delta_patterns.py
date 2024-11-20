import re

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models

from ..utils.title_resolver import (
    is_valid_fstring,
    is_valid_xpath,
    parse_title,
    resolve_title,
)
from .collection_choice_fields import Divisions, DocumentTypes


class BaseMatchPattern(models.Model):
    class MatchPatternTypeChoices(models.IntegerChoices):
        INDIVIDUAL_URL = 1, "Individual URL Pattern"
        MULTI_URL_PATTERN = 2, "Multi-URL Pattern"

    collection = models.ForeignKey(
        "Collection",
        on_delete=models.CASCADE,
        related_name="%(class)s",
        related_query_name="%(class)ss",
    )
    match_pattern = models.CharField(
        "Pattern",
        help_text="This pattern is compared against the URL of all the documents in the collection "
        "and matching documents will be returned",
    )
    match_pattern_type = models.IntegerField(choices=MatchPatternTypeChoices.choices, default=1)
    delta_urls = models.ManyToManyField(
        "DeltaUrl",
        related_name="%(class)s_delta_urls",
    )
    curated_urls = models.ManyToManyField(
        "CuratedUrl",
        related_name="%(class)s_curated_urls",
    )

    def matched_urls(self):
        """
        Find all URLs matching the pattern.
        This does not update pattern.delta_urls or pattern.curated_urls.
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        CuratedUrl = apps.get_model("sde_collections", "CuratedUrl")

        # Construct the regex pattern based on match type
        escaped_match_pattern = re.escape(self.match_pattern)
        regex_pattern = (
            f"{escaped_match_pattern}$"
            if self.match_pattern_type == self.MatchPatternTypeChoices.INDIVIDUAL_URL
            else escaped_match_pattern.replace(r"\*", ".*")
        )

        # Directly query DeltaUrl and CuratedUrl with collection filter
        matching_delta_urls = DeltaUrl.objects.filter(collection=self.collection, url__regex=regex_pattern)
        matching_curated_urls = CuratedUrl.objects.filter(collection=self.collection, url__regex=regex_pattern)

        return {
            "matching_delta_urls": matching_delta_urls,
            "matching_curated_urls": matching_curated_urls,
        }

    def refresh_url_lists(self):
        """Update the delta_urls and curated_urls ManyToMany relationships."""
        matched_urls = self.matched_urls()
        self.delta_urls.set(matched_urls["matching_delta_urls"])
        self.curated_urls.set(matched_urls["matching_curated_urls"])

    def generate_delta_url(self, curated_url, fields_to_copy=None):
        """
        Generates or updates a DeltaUrl based on a CuratedUrl.
        Only specified fields are copied if fields_to_copy is provided.
        """
        # Import DeltaUrl dynamically to avoid circular import issues
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")

        delta_url, created = DeltaUrl.objects.get_or_create(
            collection=self.collection,
            url=curated_url.url,
            defaults={field: getattr(curated_url, field) for field in (fields_to_copy or [])},
        )
        if not created and fields_to_copy:
            # Update only if certain fields are missing in DeltaUrl
            for field in fields_to_copy:
                if getattr(delta_url, field, None) in [None, ""]:
                    setattr(delta_url, field, getattr(curated_url, field))
            delta_url.save()

    def apply(self, fields_to_copy=None, update_fields=None):
        matched_urls = self.matched_urls()

        # Step 1: Generate or update DeltaUrls for each matching CuratedUrl
        for curated_url in matched_urls["matching_curated_urls"]:
            # Check if the curated_url is already linked to this pattern
            if self.curated_urls.filter(pk=curated_url.pk).exists():
                # Skip creating a DeltaUrl if the curated_url is already associated with this pattern
                continue
            self.generate_delta_url(curated_url, fields_to_copy)

        # Step 2: Apply updates to fields on matching DeltaUrls
        if update_fields:
            matched_urls["matching_delta_urls"].update(**update_fields)

        # Update ManyToMany relationships
        self.refresh_url_lists()

    def unapply(self):
        """Default unapply behavior."""
        self.delta_urls.clear()
        self.curated_urls.clear()

    def save(self, *args, **kwargs):
        """Save the pattern and apply it."""
        super().save(*args, **kwargs)
        self.apply()

    def delete(self, *args, **kwargs):
        """Delete the pattern and unapply it."""
        self.unapply()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ["match_pattern"]
        unique_together = ("collection", "match_pattern")

    def __str__(self):
        return self.match_pattern


class DeltaExcludePattern(BaseMatchPattern):
    reason = models.TextField("Reason for excluding", default="", blank=True)

    # No need to override `apply`—we use the base class logic as-is.
    # This pattern's functionality is handled by the `excluded` annotation in the manager.

    class Meta:
        verbose_name = "Delta Exclude Pattern"
        verbose_name_plural = "Delta Exclude Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaIncludePattern(BaseMatchPattern):
    # No additional logic needed for `apply`—using base class functionality.

    class Meta:
        verbose_name = "Delta Include Pattern"
        verbose_name_plural = "Delta Include Patterns"
        unique_together = ("collection", "match_pattern")


def validate_title_pattern(title_pattern_string):
    parsed_title = parse_title(title_pattern_string)

    for element in parsed_title:
        element_type, element_value = element

        if element_type == "xpath":
            if not is_valid_xpath(element_value):
                raise ValidationError(f"'xpath:{element_value}' is not a valid xpath.")  # noqa: E231
        elif element_type == "brace":
            try:
                is_valid_fstring(element_value)
            except ValueError as e:
                raise ValidationError(str(e))


class DeltaTitlePattern(BaseMatchPattern):
    title_pattern = models.CharField(
        "Title Pattern",
        help_text="This is the pattern for the new title. You can either write an exact replacement string"
        " (no quotes required) or you can write sinequa-valid code",
        validators=[validate_title_pattern],
    )

    def apply(self) -> None:
        # Dynamically get the DeltaResolvedTitle and DeltaResolvedTitleError models to avoid circular import issues
        DeltaResolvedTitle = apps.get_model("sde_collections", "DeltaResolvedTitle")
        DeltaResolvedTitleError = apps.get_model("sde_collections", "DeltaResolvedTitleError")

        matched_urls = self.matched_urls()

        # Step 1: Apply title pattern to matching DeltaUrls
        for delta_url in matched_urls["matching_delta_urls"]:
            self.apply_title_to_url(delta_url, DeltaResolvedTitle, DeltaResolvedTitleError)

        # Step 2: Check and potentially create DeltaUrls for matching CuratedUrls
        for curated_url in matched_urls["matching_curated_urls"]:
            self.create_delta_if_title_differs(curated_url, DeltaResolvedTitle, DeltaResolvedTitleError)

        # Step 3: Update ManyToMany relationships for DeltaUrls and CuratedUrls
        self.refresh_url_lists()

    def create_delta_if_title_differs(self, curated_url, DeltaResolvedTitle, DeltaResolvedTitleError):
        """
        Checks if the title generated by the pattern differs from the existing generated title
        in CuratedUrl. If it does, creates or updates a DeltaUrl with the new title.
        """
        # Calculate the title that would be generated if the pattern is applied
        context = {
            "url": curated_url.url,
            "title": curated_url.scraped_title,
            "collection": self.collection.name,
        }
        try:
            new_generated_title = resolve_title(self.title_pattern, context)

            # Compare against the existing generated title in CuratedUrl
            if curated_url.generated_title != new_generated_title:
                # Only create a DeltaUrl if the titles differ
                DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
                delta_url, created = DeltaUrl.objects.get_or_create(
                    collection=self.collection,
                    url=curated_url.url,
                    defaults={"scraped_title": curated_url.scraped_title},
                )
                delta_url.generated_title = new_generated_title
                delta_url.save()
                self.apply_title_to_url(delta_url, DeltaResolvedTitle, DeltaResolvedTitleError)

        except (ValueError, ValidationError) as e:
            self.log_title_error(curated_url, DeltaResolvedTitleError, str(e))

    def apply_title_to_url(self, url_obj, DeltaResolvedTitle, DeltaResolvedTitleError):
        """
        Applies the title pattern to a DeltaUrl or CuratedUrl and records the resolved title or errors.
        """
        context = {
            "url": url_obj.url,
            "title": url_obj.scraped_title,
            "collection": self.collection.name,
        }
        try:
            generated_title = resolve_title(self.title_pattern, context)

            # Remove existing resolved title entries for this URL
            DeltaResolvedTitle.objects.filter(delta_url=url_obj).delete()

            # Create a new resolved title entry
            DeltaResolvedTitle.objects.create(title_pattern=self, delta_url=url_obj, resolved_title=generated_title)

            # Set generated title only on DeltaUrl
            url_obj.generated_title = generated_title
            url_obj.save()

        except (ValueError, ValidationError) as e:
            self.log_title_error(url_obj, DeltaResolvedTitleError, str(e))

    def log_title_error(self, url_obj, DeltaResolvedTitleError, message):
        """Logs an error when resolving a title."""
        resolved_title_error = DeltaResolvedTitleError.objects.create(
            title_pattern=self, delta_url=url_obj, error_string=message
        )
        status_code = re.search(r"Status code: (\d+)", message)
        if status_code:
            resolved_title_error.http_status_code = int(status_code.group(1))
        resolved_title_error.save()

    def unapply(self) -> None:
        """Clears generated titles for DeltaUrls affected by this pattern and dissociates URLs from the pattern."""
        matched_urls = self.matched_urls()

        # Clear the `generated_title` for all matching DeltaUrls
        matched_urls["matching_delta_urls"].update(generated_title="")

        # Clear relationships
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Delta Title Pattern"
        verbose_name_plural = "Delta Title Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDocumentTypePattern(BaseMatchPattern):
    document_type = models.IntegerField(choices=DocumentTypes.choices)

    # We use `update_fields` in the base apply method to set `document_type`.
    def apply(self) -> None:
        super().apply(update_fields={"document_type": self.document_type})

    def unapply(self) -> None:
        """Clear document type from associated delta and curated URLs."""
        self.delta_urls.update(document_type=None)
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta:
        verbose_name = "Delta Document Type Pattern"
        verbose_name_plural = "Delta Document Type Patterns"
        unique_together = ("collection", "match_pattern")


class DeltaDivisionPattern(BaseMatchPattern):
    division = models.IntegerField(choices=Divisions.choices)

    # We use `update_fields` in the base apply method to set `division`.
    def apply(self) -> None:
        super().apply(update_fields={"division": self.division})

    def unapply(self) -> None:
        """Clear division from associated delta and curated URLs."""
        # TODO: need to double check this logic for complicated cases
        self.delta_urls.update(division=None)

    class Meta:
        verbose_name = "Delta Division Pattern"
        verbose_name_plural = "Delta Division Patterns"
        unique_together = ("collection", "match_pattern")


# @receiver(post_save, sender=DeltaTitlePattern)
# def post_save_handler(sender, instance, created, **kwargs):
#     if created:
#         transaction.on_commit(lambda: resolve_title_pattern.delay(instance.pk))

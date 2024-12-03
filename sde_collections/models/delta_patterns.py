import re
from typing import Any

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
    """Base class for all delta patterns."""

    class MatchPatternTypeChoices(models.IntegerChoices):
        INDIVIDUAL_URL = 1, "Individual URL Pattern"
        MULTI_URL_PATTERN = 2, "Multi-URL Pattern"

    collection = models.ForeignKey(
        "Collection",
        on_delete=models.CASCADE,
        related_name="%(class)ss",  # Makes collection.deltaincludepatterns.all()
        related_query_name="%(class)ss",
    )
    match_pattern = models.CharField(
        "Pattern", help_text="This pattern is compared against the URL of all documents in the collection"
    )
    match_pattern_type = models.IntegerField(choices=MatchPatternTypeChoices.choices, default=1)
    delta_urls = models.ManyToManyField(
        "DeltaUrl",
        related_name="%(class)ss",  # Makes delta_url.deltaincludepatterns.all()
    )
    curated_urls = models.ManyToManyField(
        "CuratedUrl",
        related_name="%(class)ss",  # Makes curated_url.deltaincludepatterns.all()
    )

    def get_url_match_count(self):
        """
        Get the number of unique URLs this pattern matches across both delta and curated URLs.
        """
        delta_urls = set(self.get_matching_delta_urls().values_list("url", flat=True))
        curated_urls = set(self.get_matching_curated_urls().values_list("url", flat=True))
        return len(delta_urls.union(curated_urls))

    def is_most_distinctive_pattern(self, url) -> bool:
        """
        Determine if this pattern should apply to a URL by checking if it matches
        the smallest number of URLs among all patterns that match this URL.
        Returns True if this pattern should be applied.
        """
        my_match_count = self.get_url_match_count()

        # Get patterns from same type that affect this URL
        pattern_class = self.__class__
        matching_patterns = (
            pattern_class.objects.filter(collection=self.collection)
            .filter(models.Q(delta_urls__url=url.url) | models.Q(curated_urls__url=url.url))
            .exclude(id=self.id)
            .distinct()
        )  # TODO: does this have a distinct urls, or distinct model objects.

        # If any matching pattern has a smaller URL set, don't apply
        for pattern in matching_patterns:
            if pattern.get_url_match_count() < my_match_count:
                return False

        return True

    def get_regex_pattern(self) -> str:
        """Convert the match pattern into a proper regex based on pattern type."""
        escaped_pattern = re.escape(self.match_pattern)
        if self.match_pattern_type == self.MatchPatternTypeChoices.INDIVIDUAL_URL:
            return f"{escaped_pattern}$"
        return escaped_pattern.replace(r"\*", ".*")

    def get_matching_delta_urls(self) -> models.QuerySet:
        """Get all DeltaUrls that match this pattern."""
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        regex_pattern = self.get_regex_pattern()
        return DeltaUrl.objects.filter(collection=self.collection, url__regex=regex_pattern)

    def get_matching_curated_urls(self) -> models.QuerySet:
        """Get all CuratedUrls that match this pattern."""
        CuratedUrl = apps.get_model("sde_collections", "CuratedUrl")
        regex_pattern = self.get_regex_pattern()
        return CuratedUrl.objects.filter(collection=self.collection, url__regex=regex_pattern)

    def update_affected_delta_urls_list(self) -> None:
        """Update the many-to-many relationship for matched DeltaUrls."""
        self.delta_urls.set(self.get_matching_delta_urls())

    def update_affected_curated_urls_list(self) -> None:
        """Update the many-to-many relationship for matched CuratedUrls."""
        self.curated_urls.set(self.get_matching_curated_urls())

    def apply(self) -> None:
        """Apply pattern effects. Must be implemented by subclasses."""
        raise NotImplementedError

    def unapply(self) -> None:
        """Remove pattern effects. Must be implemented by subclasses."""
        raise NotImplementedError

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.apply()

    def delete(self, *args, **kwargs) -> None:
        self.unapply()
        super().delete(*args, **kwargs)

    class Meta:
        abstract = True
        ordering = ["match_pattern"]
        unique_together = ("collection", "match_pattern")

    def __str__(self):
        return self.match_pattern


class InclusionPatternBase(BaseMatchPattern):
    """
    Base class for patterns that handle URL inclusion/exclusion.
    Both ExcludePattern and IncludePattern share the same core logic for managing
    relationships and Delta URL creation/cleanup.
    """

    class Meta(BaseMatchPattern.Meta):
        abstract = True

    def apply(self) -> None:
        """
        Apply pattern effects to matching URLs:
        1. Find new Curated URLs that match but weren't previously affected
        2. Create Delta URLs for newly affected Curated URLs if needed
        3. Update pattern relationships to manage inclusion/exclusion status
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")

        # Get QuerySet of all matching CuratedUrls
        matching_curated_urls = self.get_matching_curated_urls()

        # Find Curated URLs that match but weren't previously affected
        previously_unaffected_curated = matching_curated_urls.exclude(
            id__in=self.curated_urls.values_list("id", flat=True)
        )

        # Create Delta URLs for newly affected Curated URLs if needed
        for curated_url in previously_unaffected_curated:
            # Skip if Delta already exists
            if DeltaUrl.objects.filter(url=curated_url.url, collection=self.collection).exists():
                continue

            # Create new Delta URL copying fields from Curated URL
            fields = {
                field.name: getattr(curated_url, field.name)
                for field in curated_url._meta.fields
                if field.name not in ["id", "collection"]
            }
            fields["to_delete"] = False
            fields["collection"] = self.collection

            DeltaUrl.objects.create(**fields)

        # Update relationships - this handles inclusion/exclusion status
        self.update_affected_delta_urls_list()

    def unapply(self) -> None:
        """
        Remove this pattern's effects by:
        1. Creating Delta URLs for previously excluded Curated URLs to show they're no longer excluded/included
        2. Cleaning up any Delta URLs that are now identical to their Curated URL counterparts
           (these would have only existed to show their exclusion/inclusion)
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        CuratedUrl = apps.get_model("sde_collections", "CuratedUrl")

        # Create Delta URLs for previously affected Curated URLs
        for curated_url in self.curated_urls.all():
            fields = {
                field.name: getattr(curated_url, field.name)
                for field in curated_url._meta.fields
                if field.name not in ["id", "collection"]
            }
            fields["to_delete"] = False
            fields["collection"] = self.collection

            DeltaUrl.objects.get_or_create(**fields)

        # Clean up redundant Delta URLs
        for delta_url in self.delta_urls.filter(to_delete=False):
            try:
                curated_url = CuratedUrl.objects.get(collection=self.collection, url=delta_url.url)

                # Check if Delta is now identical to Curated
                fields_match = all(
                    getattr(delta_url, field.name) == getattr(curated_url, field.name)
                    for field in delta_url._meta.fields
                    if field.name not in ["id", "to_delete"]
                )

                if fields_match:
                    delta_url.delete()

            except CuratedUrl.DoesNotExist:
                continue

        # Clear pattern relationships
        self.delta_urls.clear()
        self.curated_urls.clear()


class DeltaExcludePattern(InclusionPatternBase):
    """Pattern for marking URLs for exclusion."""

    reason = models.TextField("Reason for excluding", default="", blank=True)

    class Meta(InclusionPatternBase.Meta):
        verbose_name = "Delta Exclude Pattern"
        verbose_name_plural = "Delta Exclude Patterns"


class DeltaIncludePattern(InclusionPatternBase):
    """Pattern for explicitly including URLs."""

    class Meta(InclusionPatternBase.Meta):
        verbose_name = "Delta Include Pattern"
        verbose_name_plural = "Delta Include Patterns"


class FieldModifyingPattern(BaseMatchPattern):
    """
    Abstract base class for patterns that modify a single field on matching URLs.
    Examples: DeltaDivisionPattern, DeltaDocumentTypePattern
    """

    class Meta(BaseMatchPattern.Meta):
        abstract = True

    def get_field_to_modify(self) -> str:
        """Return the name of the field this pattern modifies. Must be implemented by subclasses."""
        raise NotImplementedError

    def get_new_value(self) -> Any:
        """Return the new value for the field. Must be implemented by subclasses."""
        raise NotImplementedError

    def apply(self) -> None:
        """
        Apply field modification to matching URLs:
        1. Find new Curated URLs that match but weren't previously affected
        2. Create Delta URLs only for Curated URLs where the field value would change
        3. Update the pattern's list of affected URLs
        4. Set the field value on all matching Delta URLs
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")

        field = self.get_field_to_modify()
        new_value = self.get_new_value()

        # Get newly matching Curated URLs
        matching_curated_urls = self.get_matching_curated_urls()
        previously_unaffected_curated = matching_curated_urls.exclude(
            id__in=self.curated_urls.values_list("id", flat=True)
        )

        # Create DeltaUrls only where field value would change
        for curated_url in previously_unaffected_curated:
            if not self.is_most_distinctive_pattern(curated_url):
                continue

            if (
                getattr(curated_url, field) == new_value
                or DeltaUrl.objects.filter(url=curated_url.url, collection=self.collection).exists()
            ):
                continue

            fields = {
                f.name: getattr(curated_url, f.name)
                for f in curated_url._meta.fields
                if f.name not in ["id", "collection"]
            }
            fields[field] = new_value
            fields["to_delete"] = False
            fields["collection"] = self.collection

            DeltaUrl.objects.create(**fields)

        # Update all matching DeltaUrls with the new field value if this is the most distinctive pattern
        for delta_url in self.get_matching_delta_urls():
            if self.is_most_distinctive_pattern(delta_url):
                setattr(delta_url, field, new_value)
                delta_url.save()

        # Update pattern relationships
        self.update_affected_delta_urls_list()

    def unapply(self) -> None:
        """
        Remove field modifications:
        1. Create Delta URLs for affected Curated URLs to explicitly set NULL
        2. Remove field value from affected Delta URLs only if no other patterns affect them
        3. Clean up Delta URLs that become identical to their Curated URL
        """

        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        CuratedUrl = apps.get_model("sde_collections", "CuratedUrl")

        field = self.get_field_to_modify()

        # Get all affected URLs
        affected_deltas = self.delta_urls.all()
        affected_curated = self.curated_urls.all()

        # Process each affected delta URL
        for delta in affected_deltas:
            curated = CuratedUrl.objects.filter(collection=self.collection, url=delta.url).first()

            if not curated:
                # Scenario 1: Delta only - new URL
                setattr(delta, field, None)
                delta.save()
            else:
                # Scenario 2: Both exist
                setattr(delta, field, getattr(curated, field))
                delta.save()

                # Check if delta is now redundant
                fields_match = all(
                    getattr(delta, f.name) == getattr(curated, f.name)
                    for f in delta._meta.fields
                    if f.name not in ["id", "to_delete"]
                )
                if fields_match:
                    delta.delete()

        # Handle curated URLs that don't have deltas
        for curated in affected_curated:
            if not DeltaUrl.objects.filter(url=curated.url).exists():
                # Scenario 3: Curated only
                # Copy all fields from curated except the one we're nulling
                fields = {
                    f.name: getattr(curated, f.name) for f in curated._meta.fields if f.name not in ["id", "collection"]
                }
                fields[field] = None  # Set the pattern's field to None
                delta = DeltaUrl.objects.create(collection=self.collection, **fields)

        # Clear pattern relationships
        self.delta_urls.clear()
        self.curated_urls.clear()


class DeltaDocumentTypePattern(FieldModifyingPattern):
    """Pattern for setting document types."""

    document_type = models.IntegerField(choices=DocumentTypes.choices)

    def get_field_to_modify(self) -> str:
        return "document_type"

    def get_new_value(self) -> Any:
        return self.document_type

    class Meta(FieldModifyingPattern.Meta):
        verbose_name = "Delta Document Type Pattern"
        verbose_name_plural = "Delta Document Type Patterns"


class DeltaDivisionPattern(FieldModifyingPattern):
    """Pattern for setting divisions."""

    division = models.IntegerField(choices=Divisions.choices)

    def get_field_to_modify(self) -> str:
        return "division"

    def get_new_value(self) -> Any:
        return self.division

    class Meta(FieldModifyingPattern.Meta):
        verbose_name = "Delta Division Pattern"
        verbose_name_plural = "Delta Division Patterns"


def validate_title_pattern(title_pattern_string: str) -> None:
    """Validate title pattern format."""
    parsed_title = parse_title(title_pattern_string)

    for element_type, element_value in parsed_title:
        if element_type == "xpath":
            if not is_valid_xpath(element_value):
                raise ValidationError(f"Invalid xpath: {element_value}")
        elif element_type == "brace":
            try:
                is_valid_fstring(element_value)
            except ValueError as e:
                raise ValidationError(str(e))


class DeltaTitlePattern(BaseMatchPattern):
    """Pattern for modifying titles of URLs based on a template pattern."""

    title_pattern = models.CharField(
        "Title Pattern",
        help_text="Pattern for the new title. Can be an exact replacement string or sinequa-valid code",
        validators=[validate_title_pattern],
    )

    def generate_title_for_url(self, url_obj) -> tuple[str, str | None]:
        """
        Generate a new title for a URL using the pattern.
        Returns tuple of (generated_title, error_message).
        """
        context = {
            "url": url_obj.url,
            "title": url_obj.scraped_title,
            "collection": self.collection.name,
        }

        try:
            return resolve_title(self.title_pattern, context), None
        except Exception as e:
            return None, str(e)

    def apply(self) -> None:
        """
        Apply the title pattern to matching URLs:
        1. Find new Curated URLs that match but weren't previously affected
        2. Create Delta URLs only where the generated title differs
        3. Update all matching Delta URLs with new titles
        4. Track title resolution status and errors
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        DeltaResolvedTitle = apps.get_model("sde_collections", "DeltaResolvedTitle")
        DeltaResolvedTitleError = apps.get_model("sde_collections", "DeltaResolvedTitleError")

        # Get newly matching Curated URLs
        matching_curated_urls = self.get_matching_curated_urls()
        previously_unaffected_curated = matching_curated_urls.exclude(
            id__in=self.curated_urls.values_list("id", flat=True)
        )

        # Process each previously unaffected curated URL
        for curated_url in previously_unaffected_curated:
            if not self.is_most_distinctive_pattern(curated_url):
                continue

            new_title, error = self.generate_title_for_url(curated_url)

            if error:
                # Log error and continue to next URL
                DeltaResolvedTitleError.objects.create(title_pattern=self, delta_url=curated_url, error_string=error)
                continue

            # Skip if the generated title matches existing or if Delta already exists
            if (
                curated_url.generated_title == new_title
                or DeltaUrl.objects.filter(url=curated_url.url, collection=self.collection).exists()
            ):
                continue

            # Create new Delta URL with the new title
            fields = {
                field.name: getattr(curated_url, field.name)
                for field in curated_url._meta.fields
                if field.name not in ["id", "collection"]
            }
            fields["generated_title"] = new_title
            fields["to_delete"] = False
            fields["collection"] = self.collection

            delta_url = DeltaUrl.objects.create(**fields)

            # Record successful title resolution
            DeltaResolvedTitle.objects.create(title_pattern=self, delta_url=delta_url, resolved_title=new_title)

        # Update titles for all matching Delta URLs
        for delta_url in self.get_matching_delta_urls():
            if not self.is_most_distinctive_pattern(delta_url):
                continue

            new_title, error = self.generate_title_for_url(delta_url)

            if error:
                DeltaResolvedTitleError.objects.create(title_pattern=self, delta_url=delta_url, error_string=error)
                continue

            # Update title and record resolution - key change here
            DeltaResolvedTitle.objects.update_or_create(
                delta_url=delta_url,  # Only use delta_url for lookup
                defaults={"title_pattern": self, "resolved_title": new_title},
            )

            delta_url.generated_title = new_title
            delta_url.save()

        # Update pattern relationships
        self.update_affected_delta_urls_list()

    def unapply(self) -> None:
        """
        Remove title modifications:
        1. Create Delta URLs for affected Curated URLs to explicitly clear titles
        2. Remove generated titles from affected Delta URLs
        3. Clean up Delta URLs that become identical to their Curated URL
        4. Clear resolution tracking
        """
        DeltaUrl = apps.get_model("sde_collections", "DeltaUrl")
        CuratedUrl = apps.get_model("sde_collections", "CuratedUrl")
        DeltaResolvedTitle = apps.get_model("sde_collections", "DeltaResolvedTitle")
        DeltaResolvedTitleError = apps.get_model("sde_collections", "DeltaResolvedTitleError")

        # Get all affected URLs
        affected_deltas = self.delta_urls.all()
        affected_curated = self.curated_urls.all()

        # Process each affected delta URL
        for delta in affected_deltas:
            curated = CuratedUrl.objects.filter(collection=self.collection, url=delta.url).first()

            if not curated:
                # Scenario 1: Delta only - clear generated title
                delta.generated_title = ""
                delta.save()
            else:
                # Scenario 2: Both exist - revert to curated title
                delta.generated_title = curated.generated_title
                delta.save()

                # Check if delta is now redundant
                fields_match = all(
                    getattr(delta, f.name) == getattr(curated, f.name)
                    for f in delta._meta.fields
                    if f.name not in ["id", "to_delete"]
                )
                if fields_match:
                    delta.delete()

        # Handle curated URLs that don't have deltas
        for curated in affected_curated:
            if not DeltaUrl.objects.filter(url=curated.url).exists():
                # Scenario 3: Curated only - create delta with cleared title
                fields = {
                    f.name: getattr(curated, f.name) for f in curated._meta.fields if f.name not in ["id", "collection"]
                }
                fields["generated_title"] = ""
                DeltaUrl.objects.create(collection=self.collection, **fields)

        # Clear resolution tracking
        DeltaResolvedTitle.objects.filter(title_pattern=self).delete()
        DeltaResolvedTitleError.objects.filter(title_pattern=self).delete()

        # Clear pattern relationships
        self.delta_urls.clear()
        self.curated_urls.clear()

    class Meta(BaseMatchPattern.Meta):
        verbose_name = "Delta Title Pattern"
        verbose_name_plural = "Delta Title Patterns"


class DeltaResolvedTitleBase(models.Model):
    # TODO: need to understand this logic and whether we need to have these match to CuratedUrls as well

    title_pattern = models.ForeignKey(DeltaTitlePattern, on_delete=models.CASCADE)
    delta_url = models.OneToOneField("sde_collections.DeltaUrl", on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class DeltaResolvedTitle(DeltaResolvedTitleBase):
    resolved_title = models.CharField(blank=True, default="")

    class Meta:
        verbose_name = "Resolved Title"
        verbose_name_plural = "Resolved Titles"

    def save(self, *args, **kwargs):
        # Finds the linked delta URL and deletes DeltaResolvedTitleError objects linked to it
        DeltaResolvedTitleError.objects.filter(delta_url=self.delta_url).delete()
        super().save(*args, **kwargs)


class DeltaResolvedTitleError(DeltaResolvedTitleBase):
    error_string = models.TextField(null=False, blank=False)
    http_status_code = models.IntegerField(null=True, blank=True)

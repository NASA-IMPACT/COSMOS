import re

from django.apps import apps
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from sde_collections.tasks import resolve_title_pattern

from ..utils.title_resolver import (
    is_valid_fstring,
    is_valid_xpath,
    parse_title,
    resolve_title,
)
from .collection_choice_fields import DocumentTypes


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
    candidate_urls = models.ManyToManyField(
        "CandidateURL",
        related_name="%(class)s_urls",
    )

    def matched_urls(self):
        """Find all the urls matching the pattern."""
        escaped_match_pattern = re.escape(self.match_pattern)
        if self.match_pattern_type == self.MatchPatternTypeChoices.INDIVIDUAL_URL:
            return self.collection.candidate_urls.filter(url__regex=f"{escaped_match_pattern}$")
        elif self.match_pattern_type == self.MatchPatternTypeChoices.MULTI_URL_PATTERN:
            return self.collection.candidate_urls.filter(
                url__regex=escaped_match_pattern.replace(r"\*", ".*")  # allow * wildcards
            )
        else:
            raise NotImplementedError

    def _process_match_pattern(self) -> str:
        """
        Multi-Url patterns need a star at the beginning and at the end
        Individual Url Patterns need a star at the beginning
        """
        # we don't trust the bracketing stars from the system, so we remove any
        processed_pattern = self.match_pattern.strip().strip("*").strip()
        if not processed_pattern.startswith("http"):
            # if it doesn't begin with http, it must need a star at the beginning
            processed_pattern = f"*{processed_pattern}"
        if self.match_pattern_type == BaseMatchPattern.MatchPatternTypeChoices.MULTI_URL_PATTERN:
            # all multi urls should have a star at the end, but individuals should not
            processed_pattern = f"{processed_pattern}*"
        return processed_pattern

    def apply(self):
        raise NotImplementedError

    def unapply(self):
        raise NotImplementedError

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


class ExcludePattern(BaseMatchPattern):
    reason = models.TextField("Reason for excluding", default="", blank=True)

    def apply(self) -> None:
        matched_urls = self.matched_urls()
        candidate_url_ids = list(matched_urls.values_list("id", flat=True))
        self.candidate_urls.through.objects.bulk_create(
            objs=[
                ExcludePattern.candidate_urls.through(candidateurl_id=candidate_url_id, excludepattern_id=self.id)
                for candidate_url_id in candidate_url_ids
            ]
        )

    def unapply(self) -> None:
        "Unapplies automatically by deleting include pattern through objects in a cascade"
        return

    class Meta:
        """Meta definition for ExcludePattern."""

        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"
        unique_together = ("collection", "match_pattern")


class IncludePattern(BaseMatchPattern):
    def apply(self) -> None:
        matched_urls = self.matched_urls()
        candidate_url_ids = list(matched_urls.values_list("id", flat=True))
        self.candidate_urls.through.objects.bulk_create(
            objs=[
                IncludePattern.candidate_urls.through(candidateurl_id=candidate_url_id, includepattern_id=self.id)
                for candidate_url_id in candidate_url_ids
            ]
        )

    def unapply(self) -> None:
        "Unapplies automatically by deleting includepattern through objects in a cascade"
        return

    class Meta:
        """Meta definition for IncludePattern."""

        verbose_name = "Include Pattern"
        verbose_name_plural = "Include Patterns"
        unique_together = ("collection", "match_pattern")


def validate_title_pattern(title_pattern_string):
    parsed_title = parse_title(title_pattern_string)

    for element in parsed_title:
        element_type, element_value = element

        if element_type == "xpath":
            if not is_valid_xpath(element_value):
                raise ValidationError(f"'xpath:{element_value}' is not a valid xpath.")
        elif element_type == "brace":
            try:
                is_valid_fstring(element_value)
            except ValueError as e:
                raise ValidationError(str(e))


class TitlePattern(BaseMatchPattern):
    title_pattern = models.CharField(
        "Title Pattern",
        help_text="This is the pattern for the new title. You can either write an exact replacement string"
        " (no quotes required) or you can write sinequa-valid code",
        validators=[validate_title_pattern],
    )

    def apply(self) -> None:
        matched_urls = self.matched_urls()
        updated_urls = []
        ResolvedTitle = apps.get_model("sde_collections", "ResolvedTitle")
        ResolvedTitleError = apps.get_model("sde_collections", "ResolvedTitleError")

        for candidate_url in matched_urls:
            context = {
                "url": candidate_url.url,
                "title": candidate_url.scraped_title,
                "collection": self.collection.name,
            }

            try:
                generated_title = resolve_title(self.title_pattern, context)

                # check to see if the candidate url has an existing resolved title and delete it
                ResolvedTitle.objects.filter(candidate_url=candidate_url).delete()

                resolved_title = ResolvedTitle.objects.create(
                    title_pattern=self, candidate_url=candidate_url, resolved_title=generated_title
                )
                resolved_title.save()

                candidate_url.generated_title = generated_title
                candidate_url.save()

            except ValueError as e:
                message = str(e)
                resolved_title_error = ResolvedTitleError.objects.create(
                    title_pattern=self, candidate_url=candidate_url, error_string=message
                )

                status_code = re.search(r"Status code: (\d+)", message)
                if status_code:
                    resolved_title_error.http_status_code = int(status_code.group(1))

                resolved_title_error.save()

                raise ValidationError(str(e))

        TitlePatternCandidateURL = TitlePattern.candidate_urls.through
        pattern_url_associations = [
            TitlePatternCandidateURL(titlepattern_id=self.id, candidateurl_id=url.id) for url in updated_urls
        ]
        TitlePatternCandidateURL.objects.bulk_create(pattern_url_associations, ignore_conflicts=True)

    def unapply(self) -> None:
        self.candidate_urls.update(generated_title="")

    def resolve(self) -> None:
        print(f"Resolving title pattern {self.id}")

    class Meta:
        """Meta definition for TitlePattern."""

        verbose_name = "Title Pattern"
        verbose_name_plural = "Title Patterns"
        unique_together = ("collection", "match_pattern")


class DocumentTypePattern(BaseMatchPattern):
    document_type = models.IntegerField(choices=DocumentTypes.choices)

    def apply(self) -> None:
        matched_urls = self.matched_urls()
        matched_urls.update(document_type=self.document_type)
        candidate_url_ids = list(matched_urls.values_list("id", flat=True))
        self.candidate_urls.through.objects.bulk_create(
            objs=[
                DocumentTypePattern.candidate_urls.through(
                    candidateurl_id=candidate_url_id, documenttypepattern_id=self.id
                )
                for candidate_url_id in candidate_url_ids
            ]
        )

    def unapply(self) -> None:
        self.candidate_urls.update(document_type=None)

    class Meta:
        """Meta definition for DocumentTypePattern."""

        verbose_name = "Document Type Pattern"
        verbose_name_plural = "Document Type Patterns"
        unique_together = ("collection", "match_pattern")


@receiver(post_save, sender=TitlePattern)
def post_save_handler(sender, instance, created, **kwargs):
    if created:
        transaction.on_commit(lambda: resolve_title_pattern.delay(instance.pk))

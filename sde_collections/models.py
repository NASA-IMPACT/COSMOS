import re
from urllib.parse import urlparse

from django.db import models

from .sinequa_utils import Sinequa


class Collection(models.Model):
    """Model definition for Collection."""

    class Divisions(models.IntegerChoices):
        ASTROPHYSICS = 1, "Astrophysics"
        BIOLOGY = 2, "Biological and Physical Sciences"
        EARTH_SCIENCE = 3, "Earth Science"
        HELIOPHYSICS = 4, "Heliophysics"
        PLANETARY = 5, "Planetary Science"

    class UpdateFrequencies(models.IntegerChoices):
        DAILY = 1, "Daily"
        WEEKLY = 2, "Weekly"
        BIWEEKLY = 3, "Biweekly"
        MONTHLY = 4, "Monthly"

    class DocumentTypes(models.IntegerChoices):
        IMAGES = 1, "Images"
        DATA = 2, "Data"
        DOCUMENTATION = 3, "Documentation"
        SOFTWARETOOLS = 4, "Software and Tools"
        MISSIONSINSTRUMENTS = 5, "Missions and Instruments"

        @classmethod
        def lookup_by_text(cls, text):
            for choice in cls.choices:
                if choice[1].lower() == text.lower():
                    return choice[0]
            return None

    class SourceChoices(models.IntegerChoices):
        ONLY_IN_ORIGINAL = 1, "Only in original"
        BOTH = 2, "Both"
        ONLY_IN_SINEQUA_CONFIGS = 3, "Only in Sinequa configs"

    class ConnectorChoices(models.IntegerChoices):
        crawler2 = 1, "Web crawler parallel"

    name = models.CharField("Name", max_length=1024)
    machine_name = models.CharField(
        "Machine Name",
        max_length=1024,
        help_text="This is the Name value, but with only alphanumeric characters and _ instead of spaces",
    )
    config_folder = models.CharField("Config Folder", max_length=2048)
    url = models.URLField("URL", max_length=2048, blank=True)
    division = models.IntegerField(choices=Divisions.choices)
    turned_on = models.BooleanField("Turned On", default=True)
    connector = models.IntegerField(choices=ConnectorChoices.choices, default=1)

    source = models.IntegerField(choices=SourceChoices.choices)
    update_frequency = models.IntegerField(
        choices=UpdateFrequencies.choices, default=UpdateFrequencies.WEEKLY
    )
    document_type = models.IntegerField(
        choices=DocumentTypes.choices, null=True, blank=True
    )
    tree_root = models.CharField("Tree Root", max_length=1024, default="", blank=True)

    delete = models.BooleanField(default=False)

    # audit columns for production
    audit_hierarchy = models.CharField(
        "Audit Hierarchy", max_length=2048, default="", blank=True
    )
    audit_url = models.CharField("Audit URL", max_length=2048, default="", blank=True)
    audit_mapping = models.CharField(
        "Audit Mapping", max_length=2048, default="", blank=True
    )
    audit_label = models.CharField(
        "Audit Label", max_length=2048, default="", blank=True
    )
    audit_query = models.CharField(
        "Audit Query", max_length=2048, default="", blank=True
    )
    audit_duplicate_results = models.CharField(
        "Audit Duplicate Results", max_length=2048, default="", blank=True
    )
    audit_metrics = models.CharField(
        "Audit Metrics", max_length=2048, default="", blank=True
    )

    cleaning_assigned_to = models.CharField(
        "Cleaning Assigned To", max_length=128, default="", blank=True
    )

    notes = models.TextField("Notes", blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    new_collection = models.BooleanField(default=False)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def generate_machine_name(self):
        """
        Take the human readable `self.name` and create a standardized machine format
        The output will be the self.name, but only alphanumeric with _ instead of spaces
        """

        machine_name = self.name.lower().replace(" ", "_")
        machine_name = "".join(
            char for char in machine_name if char.isalnum() or char == "_"
        )

        return machine_name

    def import_metadata_from_sinequa_config(self):
        """Import metadata from Sinequa."""
        if not self.config_folder:
            return False
        sinequa = Sinequa(config_folder=self.config_folder)

        # tree root
        tree_root = sinequa.fetch_treeroot()
        self.tree_root = tree_root

        # document type
        document_type = sinequa.fetch_document_type()
        self.document_type = document_type

        self.save()

        return True

    def export_metadata_to_sinequa_config(self):
        """Export metadata to Sinequa."""
        if not self.config_folder:
            return
        sinequa = Sinequa(config_folder=self.config_folder)
        sinequa.update_treeroot(self.tree_root)
        sinequa.update_document_type(Collection.DocumentTypes(self.document_type).label)

    def __str__(self):
        """Unicode representation of Collection."""
        return self.name

    @property
    def has_folder(self):
        return self.config_folder != ""

    def save(self, *args, **kwargs):
        # Call the function to generate the value for the generated_field based on the original_field
        self.machine_name = self.generate_machine_name()

        # Call the parent class's save method
        super().save(*args, **kwargs)


class CandidateURL(models.Model):
    """A candidate URL scraped for a given collection."""

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="candidate_urls"
    )
    url = models.CharField("URL", max_length=2048)
    scraped_title = models.CharField(
        "Scraped Title",
        max_length=2048,
        default="",
        blank=True,
        help_text="This is the original title scraped by Sinequa",
    )
    generated_title = models.CharField(
        "Generated Title",
        max_length=2048,
        default="",
        blank=True,
        help_text="This is the title generated based on a Title Pattern",
    )
    level = models.IntegerField(
        "Level", default=0, blank=True, help_text="Level in the tree. Based on /."
    )
    excludes = models.ManyToManyField(
        "ExcludePattern", through="AppliedExclude", blank=True
    )

    class Meta:
        """Meta definition for Candidate URL."""

        verbose_name = "Candidate URL"
        verbose_name_plural = "Candidate URLs"
        ordering = ["url"]

    def splits(self):
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

    @property
    def excluded(self):
        return self.excludes.count() > 0

    def __str__(self):
        return self.url


class ExcludePattern(models.Model):
    """A pattern to exclude from Sinequa."""

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="exclude_patterns"
    )
    match_pattern = models.CharField(
        "Pattern",
        max_length=2048,
        help_text="This pattern is compared against the URL of all the documents in the collection "
        "and documents with a matching URL are excluded.",
    )
    reason = models.TextField("Reason for excluding", default="", blank=True)

    class Meta:
        """Meta definition for ExcludePattern."""

        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"
        unique_together = ("collection", "match_pattern")

    def __str__(self):
        return self.match_pattern

    def apply(self):
        """Apply the exclude pattern to the collection. Unapply happens when the exclude pattern is deleted."""
        applied = []
        for candidate_url in self.collection.candidate_urls.all():
            safe_match_pattern = re.escape(self.match_pattern.lstrip("*"))
            if re.search(safe_match_pattern, candidate_url.url):
                applied_exclude = AppliedExclude.objects.create(
                    candidate_url=candidate_url, exclude_pattern=self
                )
                applied.append(applied_exclude)
        return applied

    def save(self, *args, **kwargs):
        """Save the exclude pattern."""
        super().save(*args, **kwargs)
        self.apply()

    @property
    def sinequa_pattern(self):
        return f"{self.collection.url}{self.match_pattern}"


class AppliedExclude(models.Model):
    """
    When an exclude pattern is applied to a candidate URL, it creates one of these objects.
    The purpose is to keep track of what was excluded and why.
    """

    candidate_url = models.ForeignKey(CandidateURL, on_delete=models.CASCADE)
    exclude_pattern = models.ForeignKey(
        ExcludePattern, on_delete=models.CASCADE, related_name="applied_excludes"
    )

    class Meta:
        verbose_name = "Applied Exclude"
        verbose_name_plural = "Applied Excludes"

    def __str__(self):
        return f"{self.candidate_url} was excluded by {self.exclude_pattern}"


class TitlePattern(models.Model):
    """A title pattern to overwrite."""

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="title_patterns"
    )
    match_pattern = models.CharField(
        "Pattern",
        max_length=2048,
        help_text="This pattern is compared against the URL of all the documents in the collection "
        "and matching documents will have their title overwritten with the title_pattern",
    )
    title_pattern = models.CharField(
        "New Title Pattern",
        max_length=2048,
        help_text="This is the pattern for the new title. You can write your own text, as well as "
        "add references to a specific xpath or the orignal title. For example 'James Webb {scraped_title}: {xpath}'",
    )

    class Meta:
        """Meta definition for TitlePattern."""

        verbose_name = "Title Re-Write Pattern"
        verbose_name_plural = "Title Re-Write Patterns"

    def __str__(self):
        return f"{self.match_pattern}: {self.title_pattern}"

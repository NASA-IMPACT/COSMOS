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
        crawler2 = 1, "Web crawler paralle"

    name = models.CharField("Name", max_length=1024)
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

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

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

    def generate_candidate_urls(self):
        """Generate candidate URLs."""
        pass

    def __str__(self):
        """Unicode representation of Collection."""
        return self.name

    @property
    def has_folder(self):
        return self.config_folder != ""


class CandidateURL(models.Model):
    """A candidate URL scraped for a given collection."""

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    url = models.CharField("Path", max_length=2048, default="", blank=True)
    full_url = models.CharField("Full URL", max_length=4096, default="", blank=True)
    excluded = models.BooleanField(default=False)
    title = models.CharField("Title", max_length=2048, default="", blank=True)
    replacement_title = models.CharField(
        "Replacement Title",
        max_length=2048,
        default="",
        blank=True,
        help_text="If set, this title will be used instead of the scraped title."
        " You can use the original title in the replacement title like so: {title}.",
    )

    class Meta:
        """Meta definition for Candidate URL."""

        verbose_name = "Candidate URL"
        verbose_name_plural = "Candidate URLs"
        ordering = ["url"]

    def __str__(self):
        return self.url


class ExcludePattern(models.Model):
    """A pattern to exclude from Sinequa."""

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="exclude_patterns"
    )
    pattern = models.CharField("Pattern", max_length=2048)
    reason = models.TextField("Reason for excluding", default="", blank=True)

    class Meta:
        """Meta definition for ExcludePattern."""

        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"

    def __str__(self):
        return self.pattern

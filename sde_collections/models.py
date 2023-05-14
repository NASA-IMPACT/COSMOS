import re
from urllib.parse import urlparse

from django.conf import settings
from django.db import models
from slugify import slugify

from .db_to_xml import XmlEditor
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
    config_folder = models.CharField("Config Folder", max_length=2048, unique=True)
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
    cleaning_order = models.IntegerField(default=0, blank=True)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    def _process_exclude_list(self):
        """Process the exclude list."""
        exclude_list = []
        for exclude_pattern in self.exclude_patterns.all():
            if exclude_pattern.match_pattern.strip("*").strip().startswith("http"):
                exclude_list.append(f"{exclude_pattern.match_pattern}*")
            else:
                exclude_list.append(f"*{exclude_pattern.match_pattern}*")
        return exclude_list

    def generate_new_config(self):
        """Generates a new config based on the new collection template."""
        config_folder = self.config_folder
        document_type = self.document_type
        division = self.get_division_display()
        name = self.name
        tree_root = self.tree_root
        url = self.url

        URL_EXCLUDES = self._process_exclude_list()

        TITLE_RULES = []

        ORIGINAL_CONFIG_PATH = (
            settings.BASE_DIR
            / "sde_collections/xml_templates/new_collection_template.xml"
        )

        DIVISION_INDEX_MAPPING = {
            "Astrophysics": "@@Astrophysics",
            "Planetary Science": "@@Planetary",
            "Earth Science": "@@EarthScience",
            "Heliophysics": "@@Heliophysics",
            "Biological and Physical Sciences": "@@BiologicalAndPhysicalSciences",
        }

        SINEQUA_SOURCES_FOLDER = (
            settings.BASE_DIR / "sinequa_configs" / "sources" / "SMD"
        )

        # collection metadata adding
        editor = XmlEditor(ORIGINAL_CONFIG_PATH)
        editor.convert_scraper_to_indexer()
        # editor.add_id()
        editor.add_document_type(document_type)
        editor.update_or_add_element_value("visibility", "publicCollection")
        editor.update_or_add_element_value("Description", f"Webcrawler for the {name}")
        editor.update_or_add_element_value("Url", url)
        editor.update_or_add_element_value("TreeRoot", tree_root)
        editor.update_or_add_element_value(
            "ShardIndexes", DIVISION_INDEX_MAPPING[division]
        )
        editor.update_or_add_element_value("ShardingStrategy", "Balanced")

        # rule adding
        [editor.add_url_exclude(url) for url in URL_EXCLUDES]
        [editor.add_title_mapping(**title_rule) for title_rule in TITLE_RULES]

        editor.create_config_folder_and_default(SINEQUA_SOURCES_FOLDER, config_folder)
        editor.prettify_config(SINEQUA_SOURCES_FOLDER, config_folder)

    def _compute_config_folder_name(self):
        """
        Take the human readable `self.name` and create a standardized machine format
        The output will be the self.name, but only alphanumeric with _ instead of spaces
        """

        return slugify(self.name, separator="_")

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
        if not self.config_folder:
            self.config_folder = self._compute_config_folder_name()

        # Call the parent class's save method
        super().save(*args, **kwargs)


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

    def __str__(self):
        return self.url


class ExcludePattern(models.Model):
    """A pattern to exclude from Sinequa."""

    class PatternTypeChoices(models.IntegerChoices):
        INDIVIDUAL_URL = 1, "Individual URL"
        REGEX_PATTERN = 2, "Regex Pattern"

    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="exclude_patterns"
    )
    match_pattern = models.CharField(
        "Pattern",
        help_text="This pattern is compared against the URL of all the documents in the collection "
        "and documents with a matching URL are excluded.",
    )
    pattern_type = models.IntegerField(choices=PatternTypeChoices.choices, default=1)
    candidate_urls = models.ManyToManyField(CandidateURL)
    reason = models.TextField("Reason for excluding", default="", blank=True)

    class Meta:
        """Meta definition for ExcludePattern."""

        verbose_name = "Exclude Pattern"
        verbose_name_plural = "Exclude Patterns"
        unique_together = ("collection", "match_pattern")

    def __str__(self):
        return self.match_pattern

    def apply(self):
        """Apply the exclude pattern to the collection."""
        regex_search_string = f'{re.escape(self.match_pattern.strip("*"))}'
        if self.pattern_type == ExcludePattern.PatternTypeChoices.INDIVIDUAL_URL:
            regex_search_string += r"$"
        for candidate_url in self.collection.candidate_urls.filter(
            url__regex=regex_search_string
        ):
            self.candidate_urls.add(candidate_url)

    def save(self, *args, **kwargs):
        """Save the exclude pattern."""
        super().save(*args, **kwargs)
        self.apply()

    @property
    def sinequa_pattern(self):
        return f"{self.collection.url}{self.match_pattern}"


class TitlePattern(models.Model):
    """A title pattern to overwrite."""

    class MatchPatternTypeChoices(models.IntegerChoices):
        INDIVIDUAL_URL = 1, "Individual URL"
        REGEX_PATTERN = 2, "Regex Pattern"

    class TitlePatternTypeChoices(models.IntegerChoices):
        PLAIN_TEXT = 1, "Plain Text"
        MODIFIER = 2, "Modifier"
        XPATH = 3, "Xpath"

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

    # keep track of which urls the pattern is applied to so it's easy to unapply
    # candidate_urls = models.ManyToManyField(CandidateURL)
    match_pattern_type = models.IntegerField(
        choices=MatchPatternTypeChoices.choices, default=1
    )

    title_pattern_type = models.IntegerField(
        choices=TitlePatternTypeChoices.choices, default=1
    )

    def apply(self):
        """Apply the title pattern to the collection."""
        regex_search_string = f'{re.escape(self.match_pattern.strip("*"))}'
        if (
            self.match_pattern_type
            == TitlePattern.MatchPatternTypeChoices.INDIVIDUAL_URL
        ):
            regex_search_string += r"$"
        self.collection.candidate_urls.filter(url__regex=regex_search_string).update(
            generated_title=self.title_pattern
        )

    def unapply(self):
        """Unapply the title pattern to the collection."""
        regex_search_string = f'{re.escape(self.match_pattern.strip("*"))}'
        if (
            self.match_pattern_type
            == TitlePattern.MatchPatternTypeChoices.INDIVIDUAL_URL
        ):
            regex_search_string += r"$"
        self.collection.candidate_urls.filter(url__regex=regex_search_string).update(
            generated_title=""
        )

    class Meta:
        """Meta definition for TitlePattern."""

        verbose_name = "Title Re-Write Pattern"
        verbose_name_plural = "Title Re-Write Patterns"

    def __str__(self):
        return f"{self.match_pattern}: {self.title_pattern}"

    def save(self, *args, **kwargs):
        """Save the title pattern."""
        super().save(*args, **kwargs)
        self.apply()

    def delete(self, *args, **kwargs):
        """Delete the title pattern."""
        self.unapply()
        super().delete(*args, **kwargs)

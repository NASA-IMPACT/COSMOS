from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from slugify import slugify

from config_generation.db_to_xml import XmlEditor

from ..sinequa_utils import Sinequa
from .collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    SourceChoices,
    UpdateFrequencies,
)

User = get_user_model()


class Collection(models.Model):
    """Model definition for Collection."""

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

    github_issue_number = models.IntegerField("Issue Number in Github", default=0)
    notes = models.TextField("Notes", blank=True, default="")
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)
    new_collection = models.BooleanField(default=False)
    cleaning_order = models.IntegerField(default=0, blank=True)

    curation_status = models.IntegerField(
        choices=CurationStatusChoices.choices, default=1
    )
    curated_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    curation_started = models.DateTimeField("Curation Started", null=True, blank=True)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    @property
    def curation_status_button_color(self):
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
        }
        return color_choices[self.curation_status]

    def _process_exclude_list(self):
        """Process the exclude list."""
        return [
            pattern._process_match_pattern() for pattern in self.excludepattern.all()
        ]

    def _process_title_list(self):
        """Process the title list"""
        title_rules = []
        for title_pattern in self.titlepattern.all():
            processed_pattern = {
                "title_criteria": title_pattern._process_match_pattern(),
                "title_value": title_pattern.title_pattern,
            }
            title_rules.append(processed_pattern)
        return title_rules

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

    def update_existing_config(self):
        SINEQUA_SOURCES_FOLDER = (
            settings.BASE_DIR / "sinequa_configs" / "sources" / "SMD"
        )
        path = f"{SINEQUA_SOURCES_FOLDER}/{self.config_folder}/default.xml"
        editor = XmlEditor(path)

        # TODO: an argument could be made for re-writing all relevant sinequa config
        # fields here, however, the complications are worth thinking about before blindly
        # doing it, so in this v0.1 we will only do tree_root and rules

        URL_EXCLUDES = self._process_exclude_list()
        TITLE_RULES = self._process_title_list()
        editor.update_or_add_element_value("TreeRoot", self.tree_root)
        [editor.add_url_exclude(url) for url in URL_EXCLUDES]
        [editor.add_title_mapping(**title_rule) for title_rule in TITLE_RULES]
        editor._update_config_xml(path)

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

    @property
    def candidate_urls_count(self):
        return self.candidate_urls.count()

    @property
    def sinequa_configuration(self):
        return f"https://github.com/NASA-IMPACT/sde-backend/blob/master/sources/SMD/{self.config_folder}/default.xml"

    @property
    def github_issue_link(self):
        return f"https://github.com/NASA-IMPACT/sde-project/issues/{self.github_issue_number}"

    def apply_all_patterns(self):
        """Apply all the patterns."""
        for pattern in self.excludepattern.all():
            pattern.apply()
        for pattern in self.titlepattern.all():
            pattern.apply()
        for pattern in self.documenttypepattern.all():
            pattern.apply()

    def save(self, *args, **kwargs):
        # Call the function to generate the value for the generated_field based on the original_field
        if not self.config_folder:
            self.config_folder = self._compute_config_folder_name()

        # Call the parent class's save method
        super().save(*args, **kwargs)


class RequiredUrls(models.Model):
    """
    URLs listed during the research and iteration phases by a curator for a collection,
    which are expected to be indexed by that collection's scraper and indexer
    """

    url = models.URLField(
        help_text="URL which is expected to be brought in by the scraper and indexer",
    )
    collection = models.ForeignKey("Collection", on_delete=models.CASCADE)

    def __str__(self):
        return self.url

import json
import urllib.parse

from django.contrib.auth import get_user_model
from django.db import models
from slugify import slugify

from config_generation.db_to_xml import XmlEditor

from ..utils.github_helper import GitHubHandler
from .collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    SourceChoices,
    UpdateFrequencies,
    WorkflowStatusChoices,
)

User = get_user_model()


class Collection(models.Model):
    """Model definition for Collection."""

    name = models.CharField("Name", max_length=1024)
    config_folder = models.CharField("Config Folder", max_length=2048, unique=True)
    url = models.URLField("URL", max_length=2048, blank=True)
    division = models.IntegerField(choices=Divisions.choices)
    turned_on = models.BooleanField("Turned On", default=True)
    connector = models.IntegerField(
        choices=ConnectorChoices.choices, default=ConnectorChoices.CRAWLER2
    )

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
        choices=CurationStatusChoices.choices,
        default=CurationStatusChoices.NEEDS_SCRAPING,
    )
    workflow_status = models.IntegerField(
        choices=WorkflowStatusChoices.choices,
        default=WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
    )
    curated_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, null=True, blank=True
    )
    curation_started = models.DateTimeField("Curation Started", null=True, blank=True)
    has_sinequa_config = models.BooleanField(default=True)

    class Meta:
        """Meta definition for Collection."""

        verbose_name = "Collection"
        verbose_name_plural = "Collections"

    @property
    def server_url_test(self) -> str:
        base_url = "https://sciencediscoveryengine.test.nasa.gov"
        payload = {
            "name": "query-smd-primary",
            "scope": "All",
            "text": "",
            "advanced": {
                "collection": f"/SMD/{self.config_folder}/",
            },
        }
        encoded_payload = urllib.parse.quote(json.dumps(payload))
        return f"{base_url}/app/nasa-sba-smd/#/search?query={encoded_payload}"

    @property
    def curation_status_button_color(self) -> str:
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
        }
        return color_choices[self.curation_status]

    @property
    def workflow_status_button_color(self) -> str:
        color_choices = {
            1: "btn-light",
            2: "btn-danger",
            3: "btn-warning",
            4: "btn-info",
            5: "btn-success",
            6: "btn-primary",
            7: "btn-info",
            8: "btn-secondary",
            9: "btn-light",
            10: "btn-danger",
            11: "btn-warning",
            12: "btn-info",
            13: "btn-success",
            14: "btn-primary",
            15: "btn-info",
            16: "btn-secondary",
        }
        return color_choices[self.workflow_status]

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

    def _process_document_type_list(self):
        """Process the document type list"""
        document_type_rules = []
        for document_type_pattern in self.documenttypepattern.all():
            processed_pattern = {
                "criteria": document_type_pattern._process_match_pattern(),
                "document_type": document_type_pattern.get_document_type_display(),
            }
            document_type_rules.append(processed_pattern)
        return document_type_rules

    def update_config_xml(self, original_config_string):
        """
        reads from the model data and creates a config that mirrors the
            - excludes
            - title rules
            - doc types
            - tree root
        """
        editor = XmlEditor(original_config_string)

        URL_EXCLUDES = self._process_exclude_list()
        TITLE_RULES = self._process_title_list()
        DOCUMENT_TYPE_RULES = self._process_document_type_list()

        # TODO: this was creating duplicates so it was temporarily disabled
        # if self.tree_root:
        #     editor.update_or_add_element_value("TreeRoot", self.tree_root)

        for url in URL_EXCLUDES:
            editor.add_url_exclude(url)
        for title_rule in TITLE_RULES:
            editor.add_title_mapping(**title_rule)
        for rule in DOCUMENT_TYPE_RULES:
            editor.add_document_type_mapping(**rule)

        updated_config_xml_string = editor.update_config_xml()
        return updated_config_xml_string

    def _compute_config_folder_name(self) -> str:
        """
        Take the human readable `self.name` and create a standardized machine format
        The output will be the self.name, but only alphanumeric with _ instead of spaces
        """

        return slugify(self.name, separator="_")

    def import_metadata_from_sinequa_config(self) -> bool:
        """Import metadata from Sinequa."""
        if not self.config_folder:
            return False

        gh = GitHubHandler(collections=[self])
        metadata = gh.fetch_metadata()

        try:
            metadata[self.config_folder]
        except KeyError:
            return False

        print(f"Updating metadata for {self.name}")
        # tree root
        tree_root = metadata[self.config_folder]["tree_root"]
        if tree_root != self.tree_root:
            print(f"Updating tree root for {self.name} to {tree_root}")
        self.tree_root = tree_root

        # document type
        document_type = metadata[self.config_folder]["document_type"]
        if document_type != self.document_type:
            print(f"Updating document type for {self.name} to {document_type}")
        self.document_type = document_type

        # connector
        # connector = metadata[self.config_folder]["connector"]
        # if connector != self.connector:
        #     print(f"Updating connector for {self.name} to {connector}")
        # self.connector = connector

        self.save()
        print("\n\n")

        return True

    def __str__(self) -> str:
        """Unicode representation of Collection."""
        return self.name

    @property
    def has_folder(self) -> bool:
        return self.config_folder != ""

    @property
    def candidate_urls_count(self) -> int:
        return self.candidate_urls.count()

    @property
    def sinequa_configuration(self) -> str:
        if not self.has_sinequa_config:
            return ""
        return f"https://github.com/NASA-IMPACT/sde-backend/blob/master/sources/SMD/{self.config_folder}/default.xml"

    @property
    def github_issue_link(self) -> str:
        return f"https://github.com/NASA-IMPACT/sde-project/issues/{self.github_issue_number}"

    def apply_all_patterns(self) -> None:
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

    def __str__(self) -> str:
        return self.url

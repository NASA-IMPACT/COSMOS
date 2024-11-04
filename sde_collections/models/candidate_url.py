import hashlib
import os
from urllib.parse import urlparse

from django.db import models

from .collection import Collection
from .collection_choice_fields import Divisions, DocumentTypes
from .pattern import ExcludePattern, TitlePattern
from ..utils.paired_field_descriptor import PairedFieldDescriptor
from django.contrib.postgres.fields import ArrayField


class CandidateURLQuerySet(models.QuerySet):
    def with_exclusion_status(self):
        return self.annotate(
            excluded=models.Exists(
                ExcludePattern.candidate_urls.through.objects.filter(candidateurl=models.OuterRef("pk"))
            )
        )


class CandidateURLManager(models.Manager):
    def get_queryset(self):
        return CandidateURLQuerySet(self.model, using=self._db).with_exclusion_status()


class CandidateURL(models.Model):
    """A candidate URL scraped for a given collection."""

    collection = models.ForeignKey(Collection, on_delete=models.CASCADE, related_name="candidate_urls")
    url = models.CharField("URL")
    hash = models.CharField("Hash", max_length=32, blank=True, default="1")
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
    test_title = models.CharField(
        "Title on Test Server",
        default="",
        blank=True,
        help_text="This is the title present on Test Server",
    )
    production_title = models.CharField(
        "Title on Production Server",
        default="",
        blank=True,
        help_text="This is the title present on Production Server",
    )
    level = models.IntegerField("Level", default=0, blank=True, help_text="Level in the tree. Based on /.")
    visited = models.BooleanField(default=False)
    objects = CandidateURLManager()
    document_type = models.IntegerField(choices=DocumentTypes.choices, null=True)
    division = models.IntegerField(choices=Divisions.choices, null=True)
    inferenced_by = models.CharField(
        "Inferenced By",
        default="",
        blank=True,
        help_text="This keeps track of who inferenced document type",
    )
    is_pdf = models.BooleanField(
        "Is PDF",
        default=False,
        help_text="This keeps track of whether the given url is pdf or not",
    )
    present_on_test = models.BooleanField(
        "URL Present In Test Environment?",
        default=False,
        help_text="Helps keep track if the Current URL is present in test environment or not",
    )
    present_on_prod = models.BooleanField(
        "URL Present In Production?",
        default=False,
        help_text="Helps keep track if the Current URL is present in production or not",
    )
    is_tdamm = models.BooleanField("Is TDAMM?", default=False, help_text="Enable TDAMM tagging for this URL")

    TDAMM_TAG_CHOICES = [
        ("MMA_M_EM", "Messenger - EM Radiation"),
        ("MMA_M_EM_G", "Messenger - EM Radiation - Gamma rays"),
        ("MMA_M_EM_X", "Messenger - EM Radiation - X-rays"),
        ("MMA_M_EM_U", "Messenger - EM Radiation - Ultraviolet"),
        ("MMA_M_EM_O", "Messenger - EM Radiation - Optical"),
        ("MMA_M_EM_I", "Messenger - EM Radiation - Infrared"),
        ("MMA_M_EM_M", "Messenger - EM Radiation - Microwave"),
        ("MMA_M_EM_R", "Messenger - EM Radiation - Radio"),
        ("MMA_M_G", "Messenger - Gravitational Waves"),
        ("MMA_M_G_CBI", "Messenger - Gravitational Waves - Compact Binary Inspiral"),
        ("MMA_M_G_S", "Messenger - Gravitational Waves - Stochastic"),
        ("MMA_M_G_CON", "Messenger - Gravitational Waves - Continuous"),
        ("MMA_M_G_B", "Messenger - Gravitational Waves - Burst"),
        ("MMA_M_C", "Messenger - Cosmic Rays"),
        ("MMA_M_N", "Messenger - Neutrinos"),
        ("MMA_O_BI", "Objects - Binaries"),
        ("MMA_O_BI_BBH", "Objects - Binaries - Binary Black Holes"),
        ("MMA_O_BI_BNS", "Objects - Binaries - Binary Neutron Stars"),
        ("MMA_O_BI_C", "Objects - Binaries - Cataclysmic Variables"),
        ("MMA_O_BI_N", "Objects - Binaries - Neutron Star-Black Hole"),
        ("MMA_O_BI_B", "Objects - Binaries - Binary Pulsars"),
        ("MMA_O_BI_W", "Objects - Binaries - White Dwarf Binaries"),
        ("MMA_O_BH", "Objects - Black Holes"),
        ("MMA_O_BH_AGN", "Objects - Black Holes - Active Galactic Nuclei"),
        ("MMA_O_BH_IM", "Objects - Black Holes - Intermediate mass"),
        ("MMA_O_BH_STM", "Objects - Black Holes - Stellar mass"),
        ("MMA_O_BH_SUM", "Objects - Black Holes - Supermassive"),
        ("MMA_O_E", "Objects - Exoplanets"),
        ("MMA_O_N", "Objects - Neutron Stars"),
        ("MMA_O_N_M", "Objects - Neutron Stars - Magnetars"),
        ("MMA_O_N_P", "Objects - Neutron Stars - Pulsars"),
        ("MMA_O_N_PWN", "Objects - Neutron Stars - Pulsar Wind Nebula"),
        ("MMA_O_S", "Objects - Supernova Remnants"),
        ("MMA_S_F", "Signals - Fast Radio Bursts"),
        ("MMA_S_G", "Signals - Gamma-ray Bursts"),
        ("MMA_S_K", "Signals - Kilonovae"),
        ("MMA_S_N", "Signals - Novae"),
        ("MMA_S_P", "Signals - Pevatrons"),
        ("MMA_S_ST", "Signals - Stellar flares"),
        ("MMA_S_SU", "Signals - Supernovae"),
    ]

    # Define TDAMM fields but make them optional
    @property
    def tdamm_tag_manual(self):
        if hasattr(self, "_tdamm_tag_manual") and self.is_tdamm:
            return self._tdamm_tag_manual
        return None

    @tdamm_tag_manual.setter
    def tdamm_tag_manual(self, value):
        if self.is_tdamm:
            self._tdamm_tag_manual = value

    @property
    def tdamm_tag_ml(self):
        if hasattr(self, "_tdamm_tag_ml") and self.is_tdamm:
            return self._tdamm_tag_ml
        return None

    @tdamm_tag_ml.setter
    def tdamm_tag_ml(self, value):
        if self.is_tdamm:
            self._tdamm_tag_ml = value

    _tdamm_tag_manual = ArrayField(
        models.CharField(max_length=255, choices=TDAMM_TAG_CHOICES),
        blank=True,
        null=True,
        verbose_name="TDAMM Manual Tags",
        db_column="tdamm_tag_manual",
    )

    _tdamm_tag_ml = ArrayField(
        models.CharField(max_length=255, choices=TDAMM_TAG_CHOICES),
        blank=True,
        null=True,
        verbose_name="TDAMM ML Tags",
        db_column="tdamm_tag_ml",
    )

    tdamm_tag = PairedFieldDescriptor("tdamm_tag")

    class Meta:
        """Meta definition for Candidate URL."""

        verbose_name = "Candidate URL"
        verbose_name_plural = "Candidate URLs"
        ordering = ["url"]
        db_table = "sde_collections_candidateurl"

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

    def __str__(self) -> str:
        return self.url

    def save(self, *args, **kwargs):
        # Generate the hash based on the model values
        hash_string = f"{self.url}{self.generated_title}{self.document_type}"
        hash_value = hashlib.md5(hash_string.encode()).hexdigest()

        # Set the hash value
        self.hash = hash_value

        super().save(*args, **kwargs)


class ResolvedTitleBase(models.Model):
    title_pattern = models.ForeignKey(TitlePattern, on_delete=models.CASCADE)
    candidate_url = models.OneToOneField(CandidateURL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True


class ResolvedTitle(ResolvedTitleBase):
    resolved_title = models.CharField(blank=True, default="")

    class Meta:
        verbose_name = "Resolved Title"
        verbose_name_plural = "Resolved Titles"

    def save(self, *args, **kwargs):
        # Finds the linked candidate URL and deletes ResolvedTitleError objects linked to it
        ResolvedTitleError.objects.filter(candidate_url=self.candidate_url).delete()
        super().save(*args, **kwargs)


class ResolvedTitleError(ResolvedTitleBase):
    error_string = models.TextField(null=False, blank=False)
    http_status_code = models.IntegerField(null=True, blank=True)

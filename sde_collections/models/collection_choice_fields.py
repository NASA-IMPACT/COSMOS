from django.db import models


class Divisions(models.IntegerChoices):
    ASTROPHYSICS = 1, "Astrophysics"
    BIOLOGY = 2, "Biological and Physical Sciences"
    EARTH_SCIENCE = 3, "Earth Science"
    HELIOPHYSICS = 4, "Heliophysics"
    PLANETARY = 5, "Planetary Science"
    GENERAL = 6, "General"

    @classmethod
    def lookup_by_text(cls, text: str) -> int | None:
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None


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
    def lookup_by_text(cls, text: str) -> int | None:
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None


class SourceChoices(models.IntegerChoices):
    ONLY_IN_ORIGINAL = 1, "Only in original"
    BOTH = 2, "Both"
    ONLY_IN_SINEQUA_CONFIGS = 3, "Only in Sinequa configs"


class ConnectorChoices(models.IntegerChoices):
    CRAWLER2 = 1, "crawler2"
    JSON = 2, "json"
    HYPERINDEX = 3, "hyperindex"
    NO_CONNECTOR = 4, "No Connector"

    @classmethod
    def lookup_by_text(cls, text: str) -> int | None:
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None


class CurationStatusChoices(models.IntegerChoices):
    NEEDS_SCRAPING = 1, "Needs Scraping"
    READY_TO_CURATE = 2, "Ready to Curate"
    BEING_CURATED = 3, "Being Curated"
    DELETE_COMBINE_COLLECTION = 7, "Delete/Combine Collection"
    NEEDS_RESCRAPING = 4, "Needs Rescraping"
    CURATED = 5, "Curated"
    GITHUB_PR_CREATED = 8, "GitHub PR Created"
    IN_PROD = 6, "In Production"

    @classmethod
    def get_status_string(cls, value):
        for choice in cls.choices:
            if choice[0] == value:
                return choice[1]
        return "N/A"


class WorkflowStatusChoices(models.IntegerChoices):
    RESEARCH_IN_PROGRESS = 1, "Research in Progress"
    READY_FOR_ENGINEERING = 2, "Ready for Engineering"
    ENGINEERING_IN_PROGRESS = 3, "Engineering in Progress"
    READY_FOR_CURATION = 4, "Ready for Curation"
    CURATION_IN_PROGRESS = 5, "Curation in Progress"
    CURATED = 6, "Curated"
    QUALITY_FIXED = 7, "Quality Fixed"
    SECRET_DEPLOYMENT_STARTED = 8, "Secret Deployment Started"
    SECRET_DEPLOYMENT_FAILED = 9, "Secret Deployment Failed"
    READY_FOR_LRM_QUALITY_CHECK = 10, "Ready for LRM Quality Check"
    READY_FOR_FINAL_QUALITY_CHECK = 11, "Ready for Quality Check"
    QUALITY_CHECK_FAILED = 12, "QC: Failed"
    QUALITY_CHECK_MINOR = 18, "QC: Minor Issues"
    QUALITY_CHECK_PERFECT = 13, "QC: Perfect"
    PROD_PERFECT = 14, "Prod: Perfect"
    PROD_MINOR = 15, "Prod: Minor Issues"
    PROD_MAJOR = 16, "Prod: Major Issues"
    MERGE_PENDING = 17, "Code Merge Pending"
    NEEDS_DELETE = 19, "Delete from Prod"


class ReindexingStatusChoices(models.IntegerChoices):
    REINDEXING_NOT_NEEDED = 1, "Reindexing Not Needed"
    REINDEXING_NEEDED_ON_DEV = 2, "Reindexing Needed on LRM Dev"
    REINDEXING_FINISHED_ON_DEV = 3, "Reindexing Finished on LRM Dev"
    REINDEXING_READY_FOR_CURATION = 4, "Ready for Curation"
    REINDEXING_CURATED = 5, "Curated"
    REINDEXING_INDEXED_ON_PROD = 6, "Indexed on Prod"

    @classmethod
    def get_status_string(cls, value):
        for choice in cls.choices:
            if choice[0] == value:
                return choice[1]
        return "N/A"


class TDAMMTags(models.TextChoices):
    """TDAMM (Tagged Data for Multi-Messenger Astronomy) tag choices."""

    NOT_TDAMM = "Not TDAMM", "Not TDAMM"
    MMA_M_EM = "MMA_M_EM", "Messenger - EM Radiation"
    MMA_M_EM_G = "MMA_M_EM_G", "Messenger - EM Radiation - Gamma rays"
    MMA_M_EM_X = "MMA_M_EM_X", "Messenger - EM Radiation - X-rays"
    MMA_M_EM_U = "MMA_M_EM_U", "Messenger - EM Radiation - Ultraviolet"
    MMA_M_EM_O = "MMA_M_EM_O", "Messenger - EM Radiation - Optical"
    MMA_M_EM_I = "MMA_M_EM_I", "Messenger - EM Radiation - Infrared"
    MMA_M_EM_M = "MMA_M_EM_M", "Messenger - EM Radiation - Microwave"
    MMA_M_EM_R = "MMA_M_EM_R", "Messenger - EM Radiation - Radio"
    MMA_M_G = "MMA_M_G", "Messenger - Gravitational Waves"
    MMA_M_G_CBI = "MMA_M_G_CBI", "Messenger - Gravitational Waves - Compact Binary Inspiral"
    MMA_M_G_S = "MMA_M_G_S", "Messenger - Gravitational Waves - Stochastic"
    MMA_M_G_CON = "MMA_M_G_CON", "Messenger - Gravitational Waves - Continuous"
    MMA_M_G_B = "MMA_M_G_B", "Messenger - Gravitational Waves - Burst"
    MMA_M_C = "MMA_M_C", "Messenger - Cosmic Rays"
    MMA_M_N = "MMA_M_N", "Messenger - Neutrinos"
    MMA_O_BI = "MMA_O_BI", "Objects - Binaries"
    MMA_O_BI_BBH = "MMA_O_BI_BBH", "Objects - Binaries - Binary Black Holes"
    MMA_O_BI_BNS = "MMA_O_BI_BNS", "Objects - Binaries - Binary Neutron Stars"
    MMA_O_BI_C = "MMA_O_BI_C", "Objects - Binaries - Cataclysmic Variables"
    MMA_O_BI_N = "MMA_O_BI_N", "Objects - Binaries - Neutron Star-Black Hole"
    MMA_O_BI_B = "MMA_O_BI_B", "Objects - Binaries - Binary Pulsars"
    MMA_O_BI_W = "MMA_O_BI_W", "Objects - Binaries - White Dwarf Binaries"
    MMA_O_BH = "MMA_O_BH", "Objects - Black Holes"
    MMA_O_BH_AGN = "MMA_O_BH_AGN", "Objects - Black Holes - Active Galactic Nuclei"
    MMA_O_BH_IM = "MMA_O_BH_IM", "Objects - Black Holes - Intermediate mass"
    MMA_O_BH_STM = "MMA_O_BH_STM", "Objects - Black Holes - Stellar mass"
    MMA_O_BH_SUM = "MMA_O_BH_SUM", "Objects - Black Holes - Supermassive"
    MMA_O_E = "MMA_O_E", "Objects - Exoplanets"
    MMA_O_N = "MMA_O_N", "Objects - Neutron Stars"
    MMA_O_N_M = "MMA_O_N_M", "Objects - Neutron Stars - Magnetars"
    MMA_O_N_P = "MMA_O_N_P", "Objects - Neutron Stars - Pulsars"
    MMA_O_N_PWN = "MMA_O_N_PWN", "Objects - Neutron Stars - Pulsar Wind Nebula"
    MMA_O_S = "MMA_O_S", "Objects - Supernova Remnants"
    MMA_S_F = "MMA_S_F", "Signals - Fast Radio Bursts"
    MMA_S_G = "MMA_S_G", "Signals - Gamma-ray Bursts"
    MMA_S_K = "MMA_S_K", "Signals - Kilonovae"
    MMA_S_N = "MMA_S_N", "Signals - Novae"
    MMA_S_P = "MMA_S_P", "Signals - Pevatrons"
    MMA_S_ST = "MMA_S_ST", "Signals - Stellar flares"
    MMA_S_SU = "MMA_S_SU", "Signals - Supernovae"

    @classmethod
    def lookup_by_text(cls, text: str) -> str | None:
        """Look up a TDAMM tag by its display text."""
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None

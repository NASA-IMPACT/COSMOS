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
    QUALITY_CHECK_FAILED = 12, "Quality Check Failed"
    READY_FOR_PUBLIC_PROD = 13, "Ready for Public Production"
    PERFECT_ON_PROD = 14, "Perfect and on Production"
    LOW_PRIORITY_PROBLEMS_ON_PROD = 15, "Low Priority Problems on Production"
    HIGH_PRIORITY_PROBLEMS_ON_PROD = 16, "High Priority Problems on Production, only for old sources"
    MERGE_PENDING = 17, "Code Merge Pending"

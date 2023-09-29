from django.db import models


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
    TRAININGANDEDUCATION = 6, "Training and Education"

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
    COLLECTION_CREATED = 1, "Collection Created"
    UNENGINEERED = 2, "Unengineered"
    ENGINEERING_IN_PROGRESS = 3, "Engineering In Progress"
    ENGINEERING_DONE_NO_URLS = 4, "Engineering Completed But No URL's Yet"
    URLS_DONE = 5, "URL'S Generated"
    READY_FOR_CURATION = 6, "Ready For Curation"
    BEING_CURATED = 7, "Being Curated"
    CURATED = 8, "Curated"
    FINAL_CODE_REVIEWED = 9, "Final Code Reviewed"
    DEPLOYED_TO_TEST = 10, "Deployed To Test"
    RUNNING_ON_TEST_COMPLETED = 11, "Completed Running On Test Server"
    QUALITY_CHECK_IN_PROGRESS = 12, "Quality Check In Progress"
    QUALITY_CHECK_FINISHED = 13, "Quality Check Completed"
    DEPLOYED_TO_PROD = 14, "Deployed To Production"
    FINISHED_RUNNING_ON_PROD = 15, "Finished Running on Production"

    @classmethod
    def get_status_string(cls, value):
        for choice in cls.choices:
            if choice[0] == value:
                return choice[1]
        return "N/A"

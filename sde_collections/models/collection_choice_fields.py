from django.db import models


class Divisions(models.IntegerChoices):
    ASTROPHYSICS = 1, "Astrophysics"
    BIOLOGY = 2, "Biological and Physical Sciences"
    EARTH_SCIENCE = 3, "Earth Science"
    HELIOPHYSICS = 4, "Heliophysics"
    PLANETARY = 5, "Planetary Science"

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
    # someone has started making a new collection, but they aren't done
    RESEARCH_IN_PROGRESS = 1, "Research in Progress"
    # someone finished inputing the collection details. finishing move caused a config to be created and sent to github
    CONFIG_CREATED = 2, "Config Created"
    # someone has claimed this collection for dev work on a server, and are working on it
    ENGINEERING_IN_PROGRESS = 3, "Engineering in Progress"
    # finished config code has been merged into the dev branch via PR, but urls may not be finished scraping
    ENGINEERING_COMPLETED = 4, "Engineering Completed"
    # config is on dev branch, and urls are fully scraped and imported into the webapp
    URLS_GENERATED = 5, "URLs Generated and Ready to Curate"
    # someone has claimed the collection and is in the process of curating it
    CURATION_IN_PROGRESS = 6, "Curation in Progress"
    # curation is finished, and this action sent a pr to github
    CURATED = 7, "Curated"
    # code made by webapp was reviewed and merged to test branch. status exists bc of the lag between review and deploy
    CURATION_CODE_REVIEWED = 8, "Curation Code Reviewed"
    # test branch code is deployed to test server and indexing has been kicked off
    TEST_DEPLOYMENT_COMPLETED = 9, "Test Deployment Completed"
    TEST_INDEXING_COMPLETED = 10, "Test Indexing Completed"
    TEST_QUALITY_IN_PROGRESS = 11, "Test Quality Checks in Progress"
    TEST_QUALITY_COMPLETE = 12, "Test Quality Checks Completed"
    # test branch code is deployed to test server and indexing has been kicked off
    PROD_DEPLOYMENT_COMPLETED = 13, "Production Deployment Completed"
    PROD_INDEXING_COMPLETED = 14, "Production Indexing Completed"
    PROD_QUALITY_IN_PROGRESS = 15, "Production Quality Checks in Progress"
    PROD_QUALITY_COMPLETE = 16, "Production Quality Checks Completed"

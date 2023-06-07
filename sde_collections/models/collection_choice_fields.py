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


class CurationStatusChoices(models.IntegerChoices):
    NEEDS_SCRAPING = 1, "Needs Scraping"
    READY_TO_CURATE = 2, "Ready to Curate"
    BEING_CURATED = 3, "Being Curated"
    DELETE_COMBINE_COLLECTION = 7, "Delete/Combine Collection"
    NEEDS_RESCRAPING = 4, "Needs Rescraping"
    CURATED = 5, "Curated"
    IN_PROD = 6, "In Production"

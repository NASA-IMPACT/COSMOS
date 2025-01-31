# sde_collections/models/inference.py
from django.db import models

from .collection import Collection


class ClassificationTypes(models.IntegerChoices):
    TDAMM = 1, "TDAMM Classification"
    DIVISION = 2, "Division Classification"

    @classmethod
    def get_model_identifier(cls, classification_type: int) -> str:
        """Get the inference API model identifier for a classification type"""
        MODEL_IDENTIFIERS = {
            cls.TDAMM: "tdamm_classifier",
            cls.DIVISION: "division_classifier",
        }
        return MODEL_IDENTIFIERS.get(classification_type)

    @classmethod
    def lookup_by_text(cls, text: str) -> int | None:
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None


class InferenceStatusChoices(models.IntegerChoices):
    QUEUED = 1, "Queued"
    IN_PROGRESS = 2, "In Progress"
    COMPLETED = 3, "Completed"
    FAILED = 4, "Failed"

    @classmethod
    def lookup_by_text(cls, text: str) -> int | None:
        for choice in cls.choices:
            if choice[1].lower() == text.lower():
                return choice[0]
        return None


class InferenceJob(models.Model):
    collection = models.ForeignKey(Collection, on_delete=models.CASCADE)
    classification_type = models.IntegerField(choices=ClassificationTypes.choices)
    status = models.IntegerField(choices=InferenceStatusChoices.choices, default=InferenceStatusChoices.QUEUED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    results = models.JSONField(null=True, blank=True)

    external_job_id = models.CharField(max_length=255, null=True, blank=True)

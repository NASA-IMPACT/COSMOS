# inference/models/inference_choice_fields.py
from django.db import models


class ClassificationType(models.IntegerChoices):
    TDAMM = 1, "TDAMM Classification"
    DIVISION = 2, "Division Classification"


class InferenceJobStatus(models.IntegerChoices):
    QUEUED = 1, "Queued"
    PENDING = 2, "Pending"
    COMPLETED = 3, "Completed"
    FAILED = 4, "Failed"
    CANCELLED = 5, "Cancelled"


class ExternalJobStatus(models.IntegerChoices):
    """Mirror the API's job status options"""

    QUEUED = 1, "Queued"
    PENDING = 2, "Pending"
    COMPLETED = 3, "Completed"
    FAILED = 4, "Failed"
    CANCELLED = 5, "Cancelled"
    NOT_FOUND = 6, "Not Found"
    UNKNOWN = 7, "Unknown"

    @classmethod
    def from_api_status(cls, api_status: str) -> int:
        """Convert API string status to our integer status"""
        status_map = {
            "queued": cls.QUEUED,
            "pending": cls.PENDING,
            "completed": cls.COMPLETED,
            "failed": cls.FAILED,
            "cancelled": cls.CANCELLED,
            "not_found": cls.NOT_FOUND,
            "unknown": cls.UNKNOWN,
        }
        return status_map.get(api_status.lower(), cls.UNKNOWN)

    @classmethod
    def to_api_status(cls, status: int) -> str:
        """Convert our integer status to API string status"""
        status_map = {
            cls.QUEUED: "queued",
            cls.PENDING: "pending",
            cls.COMPLETED: "completed",
            cls.FAILED: "failed",
            cls.CANCELLED: "cancelled",
            cls.NOT_FOUND: "not_found",
            cls.UNKNOWN: "unknown",
        }
        return status_map.get(status, "unknown")

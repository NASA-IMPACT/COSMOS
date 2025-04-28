# inference/models/__init__.py
from .inference import ExternalJob, InferenceJob, ModelVersion
from .inference_choice_fields import (
    ClassificationType,
    ExternalJobStatus,
    InferenceJobStatus,
)

__all__ = [
    "ClassificationType",
    "ExternalJobStatus",
    "InferenceJobStatus",
    "ExternalJob",
    "InferenceJob",
    "ModelVersion",
]

# inference/models/__init__.py
from .inference import ExternalJob, InferenceJob, ModelVersion  # noqa
from .inference_choice_fields import (  # noqa
    ClassificationType,
    ExternalJobStatus,
    InferenceJobStatus,
)

__all__ = [
    "ClassificationType",
    "InferenceJobStatus",
    "ExternalJobStatus",
    "ModelVersion",
    "InferenceJob",
    "ExternalJob",
]

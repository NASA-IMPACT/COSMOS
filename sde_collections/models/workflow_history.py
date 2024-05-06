from django.db import models
from django.contrib.auth import get_user_model
from .collection import Collection
from .collection_choice_fields import (
    ConnectorChoices,
    CurationStatusChoices,
    Divisions,
    DocumentTypes,
    SourceChoices,
    UpdateFrequencies,
    WorkflowStatusChoices,
)

User = get_user_model()


class WorkflowHistory(models.Model):
    collection = models.ForeignKey(
        Collection, on_delete=models.CASCADE, related_name="workflow_history", null=True
    )    
    workflow_status = models.IntegerField(
        choices=WorkflowStatusChoices.choices,
        default=WorkflowStatusChoices.RESEARCH_IN_PROGRESS,
    )
    curated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (self.collection_name + self.workflow_status)
from django.db import models


class IndexDispatch(models.Model):
    """One row per WEB_COSMOS indexing dispatch (test or prod target).

    Required because CELERY_RESULT_BACKEND = None means Celery task state cannot be
    polled: dispatched_at is the stall-timeout reference (mirroring ScrapeDispatch), and
    the COSMOS-minted run_id namespaces every S3 artifact, so an old run's status.json
    can never satisfy a newer dispatch — no LastModified freshness rule needed.
    """

    TARGET_CHOICES = [("test", "test"), ("prod", "prod")]

    collection = models.ForeignKey(
        "sde_collections.Collection",
        on_delete=models.CASCADE,
        related_name="index_dispatches",
    )
    run_id = models.CharField(max_length=64)
    target = models.CharField(max_length=8, choices=TARGET_CHOICES)
    task_arn = models.CharField(max_length=256, blank=True, default="")
    # The workflow status the collection entered the dispatch with — a succeeded prod run
    # mirrors QC_PERFECT/QC_MINOR onto PROD_PERFECT/PROD_MINOR (WORKFLOW.md step 30).
    previous_workflow_status = models.IntegerField(null=True, blank=True)
    dispatched_at = models.DateTimeField(auto_now_add=True)
    # Set when the poller resolves the run (success, failure, or stall); resolved rows
    # are never polled again, which also keeps the Slack report to a single post.
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-dispatched_at"]
        verbose_name_plural = "Index Dispatches"

    def __str__(self):
        return f"{self.collection.config_folder} -> {self.target} ({self.run_id})"

from django.db import models


class ScraperConfigOverride(models.Model):
    """Per-collection overrides merged onto the crawler's own defaults.

    All fields nullable: only non-null values are emitted into the job JSON,
    because crawl4ai's merge_job() skips None. Curators edit these in the admin
    console (WORKFLOW.md step 6).
    """

    collection = models.OneToOneField(
        "sde_collections.Collection",
        on_delete=models.CASCADE,
        related_name="scraper_config",
    )
    max_pages = models.PositiveIntegerField(null=True, blank=True, help_text="Crawler cap: 100,000")
    depth_limit = models.PositiveIntegerField(null=True, blank=True)
    delay = models.FloatField(null=True, blank=True, help_text="Seconds between requests (crawler default 0.25)")
    concurrent_requests = models.PositiveSmallIntegerField(null=True, blank=True)
    obey_robots = models.BooleanField(null=True, blank=True)
    include_subdomains = models.BooleanField(null=True, blank=True)

    class Meta:
        verbose_name = "Scraper Config Override"

    def __str__(self):
        return f"Scraper overrides for {self.collection.config_folder}"


class ScrapeDispatch(models.Model):
    """One row per SSM dispatch. Two jobs: (1) give the poller a freshness reference —
    S3 results older than dispatched_at belong to a previous run and must be ignored;
    (2) give the stall timeout a start time. Never deleted; latest row per collection wins.
    """

    collection = models.ForeignKey(
        "sde_collections.Collection",
        on_delete=models.CASCADE,
        related_name="scrape_dispatches",
    )
    dispatched_at = models.DateTimeField(auto_now_add=True)
    ssm_command_id = models.CharField(max_length=64)

    class Meta:
        ordering = ["-dispatched_at"]
        verbose_name_plural = "Scrape Dispatches"

    def __str__(self):
        return f"{self.collection.config_folder} @ {self.dispatched_at:%Y-%m-%d %H:%M:%S} ({self.ssm_command_id})"

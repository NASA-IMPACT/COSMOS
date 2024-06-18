from django.db import models


class EnvironmentalJusticeRow(models.Model):
    """
    Environmental Justice data from the spreadsheet
    """

    dataset = models.CharField("Dataset", blank=True, default="")
    description = models.CharField("Description", blank=True, default="")
    description_simplified = models.CharField(
        "Description Simplified", blank=True, default=""
    )
    indicators = models.CharField("Indicators", blank=True, default="")
    intended_use = models.CharField("Intended Use", blank=True, default="")
    latency = models.CharField("Latency", blank=True, default="")
    limitations = models.CharField("Limitations", blank=True, default="")
    project = models.CharField("Project", blank=True, default="")
    source_link = models.CharField("Source Link", blank=True, default="")
    strengths = models.CharField("Strengths", blank=True, default="")

    # fields that needs cleaning
    format = models.CharField("Format", blank=True, default="")
    geographic_coverage = models.CharField(
        "Geographic Coverage", blank=True, default=""
    )
    data_visualization = models.CharField("Data Visualization", blank=True, default="")
    spatial_resolution = models.CharField("Spatial Resolution", blank=True, default="")
    temporal_extent = models.CharField("Temporal Extent", blank=True, default="")
    temporal_resolution = models.CharField(
        "Temporal Resolution", blank=True, default=""
    )

    sde_link = models.CharField("SDE Link", default="", blank=True)

    class Meta:
        verbose_name = "Environmental Justice Row"
        verbose_name_plural = "Environmental Justice Rows"

    def __str__(self):
        return self.dataset

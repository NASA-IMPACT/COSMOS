from django.db import models


class EnvironmentalJusticeRow(models.Model):
    """
    Environmental Justice data from the spreadsheet
    """

    dataset = models.CharField("Dataset")
    description = models.CharField("Description")
    description_simplified = models.CharField("Description Simplified")
    indicators = models.CharField("Indicators")
    intended_use = models.CharField("Intended Use")
    latency = models.CharField("Latency")
    limitations = models.CharField("Limitations")
    project = models.CharField("Project")
    source_link = models.CharField("Source Link")
    strengths = models.CharField("Strengths")

    # fields that needs cleaning
    format = models.CharField("Format")
    geographic_coverage = models.CharField("Geographic Coverage")
    data_visualization = models.CharField("Data Visualization")
    spatial_resolution = models.CharField("Spatial Resolution")
    temporal_extent = models.CharField("Temporal Extent")
    temporal_resolution = models.CharField("Temporal Resolution")

    sde_links = models.CharField("SDE Links")

    class Meta:
        verbose_name = "Environmental Justice Row"
        verbose_name_plural = "Environmental Justice Rows"

    def __str__(self):
        return self.dataset

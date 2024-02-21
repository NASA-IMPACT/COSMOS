from rest_framework import serializers

from .models import EnvironmentalJusticeRow


class EnvironmentalJusticeRowSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EnvironmentalJusticeRow
        fields = [
            "dataset",
            "description",
            "description_simplified",
            "indicators",
            "intended_use",
            "latency",
            "limitations",
            "project",
            "source_link",
            "strengths",
            "format",
            "geographic_coverage",
            "data_visualization",
            "spatial_resolution",
            "temporal_extent",
            "temporal_resolution",
            "sde_links",
        ]

"""
Loads preprocessed EJ dump and creates database entries.

See README.md for more information.
"""

import json

from environmental_justice.models import EnvironmentalJusticeRow


def process_ej_dump(file_path: str) -> None:
    """Process EJ dump file and create database entries."""

    data_source = EnvironmentalJusticeRow.DataSourceChoices.ML_PRODUCTION

    # Clear existing data
    EnvironmentalJusticeRow.objects.filter(data_source=data_source).delete()

    # Load the preprocessed data
    with open(file_path) as f:
        clean_data = json.load(f)

    # Create database entries
    for entry in clean_data:
        ej_row = EnvironmentalJusticeRow(
            data_source=data_source,
            sde_link=entry["sde_link"],
            dataset=entry["dataset"],
            description=entry["description"],
            description_simplified="",  # This field exists in model but not in data
            # I think the "limitations" in SDE is equivalent to "weaknesses" from emily's data
            limitations=entry["weaknesses"],
            format=entry["format"],
            temporal_extent=entry["temporal_extent"],
            intended_use=entry["intended_use"],
            source_link=entry["source_link"],
            indicators=entry["indicators"],
            strengths=entry["strengths"],
            latency=entry["latency"],
            geographic_coverage=entry["geographic_coverage"],
            data_visualization=entry["data_visualization"],
            temporal_resolution=entry["temporal_resolution"],
            spatial_resolution=entry["spatial_resolution"],
            project=entry["projects"],  # Changed from 'projects' to 'project' to match model
        )
        ej_row.save()


process_ej_dump("backups/ej_dump_20241203_170124.json")

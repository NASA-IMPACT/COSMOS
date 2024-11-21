"""
Loads preprocessed EJ dump and creates database entries.

See README.md for more information.
"""

import json

from environmental_justice.models import EnvironmentalJusticeRow


def process_ej_dump(file_path: str) -> None:
    """Process EJ dump file and create database entries."""

    destination_server = EnvironmentalJusticeRow.DestinationServerChoices.DEV

    # Clear existing data
    EnvironmentalJusticeRow.objects.filter(destination_server=destination_server).delete()

    # Load the preprocessed data
    with open(file_path) as f:
        clean_data = json.load(f)

    # Create database entries
    for entry in clean_data:
        ej_row = EnvironmentalJusticeRow(
            destination_server=destination_server,
            sde_link=entry["sde_link"],
            dataset=entry["dataset"],
            description=entry["description"],
            limitations=entry["limitations"],
            format=entry["format"],
            temporal_extent=entry["temporal_extent"],
            intended_use=entry["intended_use"],
            source_link=entry["source_link"],
            indicators=entry["indicators"],
            strengths=entry["strengths"],
            weaknesses=entry["weaknesses"],
            latency=entry["latency"],
            geographic_coverage=entry["geographic_coverage"],
            data_visualization=entry["data_visualization"],
            temporal_resolution=entry["temporal_resolution"],
            spatial_resolution=entry["spatial_resolution"],
            projects=entry["projects"],
        )
        ej_row.save()


process_ej_dump("backups/ej_dump_20241017_133151.json")

""""
    docker-compose -f local.yml run --rm django python manage.py export_urls_to_csv \
        --output physics_of_the_cosmos.csv --collections physics_of_the_cosmos

"""

import csv
import json
import os
from pathlib import Path

from django.apps import apps
from django.core.management.base import BaseCommand

from sde_collections.models.collection import Collection
from sde_collections.models.collection_choice_fields import Divisions, DocumentTypes


class Command(BaseCommand):
    help = "Export URLs from DumpUrl, DeltaUrl, or CuratedUrl models to CSV"

    def add_arguments(self, parser):
        parser.add_argument(
            "--model",
            type=str,
            default="CuratedUrl",
            choices=["DumpUrl", "DeltaUrl", "CuratedUrl"],
            help="Model to export (default: CuratedUrl)",
        )
        parser.add_argument(
            "--collections", nargs="+", type=str, help="Collection config_folders to filter by (default: all)"
        )
        parser.add_argument(
            "--output", type=str, default="exported_urls.csv", help="Output CSV file path (default: exported_urls.csv)"
        )
        parser.add_argument(
            "--batch-size", type=int, default=1000, help="Number of records to process in each batch (default: 1000)"
        )
        parser.add_argument(
            "--full_text", action="store_true", default=False, help="Include full text in export (default: False)"
        )

    def handle(self, *args, **options):
        model_name = options["model"]
        collection_folders = options["collections"]
        output_file = options["output"]
        batch_size = options["batch_size"]

        csv_exports_dir = Path("csv_exports")
        csv_exports_dir.mkdir(parents=True, exist_ok=True)

        output_file = os.path.join(csv_exports_dir, os.path.basename(output_file))

        self.stdout.write(f"Exporting {model_name} to {output_file}")

        # Get the model class
        model_class = apps.get_model("sde_collections", model_name)

        # Build the queryset
        queryset = model_class.objects.all()

        # Filter by collections if specified
        if collection_folders:
            collections = Collection.objects.filter(config_folder__in=collection_folders)
            if not collections.exists():
                self.stderr.write(self.style.ERROR("No collections found with the specified folder names"))
                return
            queryset = queryset.filter(collection__in=collections)
            self.stdout.write(f"Filtering by {len(collections)} collections")

        # Get total count for progress reporting
        total_count = queryset.count()
        if total_count == 0:
            self.stdout.write(self.style.WARNING(f"No {model_name} records found matching the criteria"))
            return

        self.stdout.write(f"Found {total_count} records to export")

        # Define all fields to export
        base_fields = [
            "url",
            "scraped_title",
            "generated_title",
            "document_type",
            "division",
        ]

        # Add scraped_text only if full_text is True
        if options["full_text"]:
            base_fields.append("scraped_text")
            self.stdout.write("Including full text content in export")
        else:
            self.stdout.write("Excluding full text content from export (use --full_text to include)")

        # Add paired field tags separately
        tag_fields = ["tdamm_tag_manual", "tdamm_tag_ml"]

        # Add model-specific fields
        model_specific_fields = []
        if model_name == "DeltaUrl":
            model_specific_fields.append("to_delete")

        # Add collection field
        collection_fields = ["collection__name", "collection__config_folder"]

        # Combine all fields
        fields = base_fields + tag_fields + model_specific_fields + collection_fields

        # Get choice dictionaries for lookup
        document_type_choices = dict(DocumentTypes.choices)
        division_choices = dict(Divisions.choices)

        # Write to CSV
        try:
            with open(output_file, "w", newline="", encoding="utf-8") as csv_file:
                writer = csv.writer(csv_file)

                # Write header
                writer.writerow(fields)

                # Write data rows in batches
                processed_count = 0
                for i in range(0, total_count, batch_size):
                    batch = queryset[i : i + batch_size]

                    for obj in batch:
                        row = []
                        for field in fields:
                            if field == "collection__name":
                                value = obj.collection.name
                            elif field == "collection__config_folder":
                                value = obj.collection.config_folder
                            elif field == "document_type":
                                doc_type = getattr(obj, field)
                                if doc_type is not None:
                                    value = document_type_choices.get(doc_type, str(doc_type))
                                else:
                                    value = ""
                            elif field == "division":
                                div = getattr(obj, field)
                                if div is not None:
                                    value = division_choices.get(div, str(div))
                                else:
                                    value = ""
                            elif field in tag_fields:
                                tags = getattr(obj, field)
                                if tags:
                                    value = json.dumps(tags)
                                else:
                                    value = ""
                            else:
                                value = getattr(obj, field, "")
                            row.append(value)
                        writer.writerow(row)
                        processed_count += 1

                    # Report progress
                    progress_pct = processed_count / total_count * 100
                    self.stdout.write(f"Processed {processed_count}/{total_count} records ({progress_pct:.1f}%)")

                self.stdout.write(self.style.SUCCESS(f"Successfully exported {processed_count} URLs to {output_file}"))

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error exporting to CSV: {e}"))
            raise

# Generated by Django 4.2 on 2023-06-03 20:09

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0024_alter_collection_curation_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="documenttypepattern",
            name="match_pattern_type",
            field=models.IntegerField(
                choices=[(1, "Individual URL Pattern"), (2, "Multi-URL Pattern")],
                default=1,
            ),
        ),
        migrations.AlterField(
            model_name="excludepattern",
            name="match_pattern_type",
            field=models.IntegerField(
                choices=[(1, "Individual URL Pattern"), (2, "Multi-URL Pattern")],
                default=1,
            ),
        ),
        migrations.AlterField(
            model_name="titlepattern",
            name="match_pattern_type",
            field=models.IntegerField(
                choices=[(1, "Individual URL Pattern"), (2, "Multi-URL Pattern")],
                default=1,
            ),
        ),
    ]
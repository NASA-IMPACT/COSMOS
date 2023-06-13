# Generated by Django 4.2.2 on 2023-06-13 15:45

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("sde_collections", "0026_alter_collection_curation_status_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collection",
            name="connector",
            field=models.IntegerField(
                choices=[
                    (1, "crawler2"),
                    (2, "json"),
                    (3, "hyperindex"),
                    (4, "No Connector"),
                ],
                default=1,
            ),
        ),
    ]

# Generated by Django 4.2.9 on 2024-05-23 21:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("sde_collections", "0053_alter_collection_url"),
    ]

    operations = [
        migrations.AddField(
            model_name="resolvedtitle",
            name="active",
            field=models.BooleanField(default=False),
        ),
    ]
from django.db import migrations, models


def set_default_destination_server(apps, schema_editor):
    EnvironmentalJusticeRow = apps.get_model("environmental_justice", "EnvironmentalJusticeRow")
    EnvironmentalJusticeRow.objects.filter(destination_server="").update(destination_server="prod")


class Migration(migrations.Migration):

    dependencies = [
        ("environmental_justice", "0004_alter_environmentaljusticerow_data_visualization_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="environmentaljusticerow",
            name="destination_server",
            field=models.CharField(
                blank=True,
                choices=[("dev", "Development"), ("test", "Testing"), ("prod", "Production")],
                default="",
                max_length=10,
                verbose_name="Destination Server",
            ),
        ),
        migrations.RunPython(set_default_destination_server),
    ]

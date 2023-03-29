# Generated by Django 4.0.10 on 2023-03-29 01:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sde_collections', '0008_candidateurl_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='collection',
            name='audit_duplicate_results',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Duplicate Results'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_hierarchy',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Hierarchy'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_label',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Label'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_mapping',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Mapping'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_metrics',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Metrics'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_query',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit Query'),
        ),
        migrations.AddField(
            model_name='collection',
            name='audit_url',
            field=models.CharField(default='', max_length=2048, verbose_name='Audit URL'),
        ),
        migrations.AddField(
            model_name='collection',
            name='cleaning_assigned_to',
            field=models.CharField(default='', max_length=128, verbose_name='Cleaning Assigned To'),
        ),
        migrations.AddField(
            model_name='collection',
            name='delete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='collection',
            name='document_type',
            field=models.IntegerField(blank=True, choices=[(1, 'Images'), (2, 'Data'), (3, 'Documentation'), (4, 'Software and Tools'), (5, 'Missions and Instruments')], null=True),
        ),
        migrations.AddField(
            model_name='collection',
            name='notes',
            field=models.TextField(blank=True, default='', verbose_name='Notes'),
        ),
        migrations.AddField(
            model_name='collection',
            name='source',
            field=models.IntegerField(choices=[(1, 'Only in original'), (2, 'Both'), (3, 'Only in Sinequa Configs')], default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='collection',
            name='tree_root',
            field=models.CharField(default='', max_length=1024, verbose_name='Tree Root'),
        ),
        migrations.AddField(
            model_name='collection',
            name='update_frequency',
            field=models.IntegerField(choices=[(1, 'Daily'), (2, 'Weekly'), (3, 'Monthly')], default=2),
        ),
        migrations.AlterField(
            model_name='collection',
            name='division',
            field=models.IntegerField(choices=[(1, 'Astrophysics'), (2, 'Biological and Physical Sciences'), (3, 'Earth Science'), (4, 'Heliophysics'), (5, 'Planetary Science')]),
        ),
        migrations.DeleteModel(
            name='Division',
        ),
    ]

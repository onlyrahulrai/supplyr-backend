# Generated by Django 3.0.8 on 2020-07-27 09:02

from django.db import migrations, models
import supplyr.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20200725_1602'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='gst_certificate',
            field=models.FileField(blank=True, max_length=150, null=True, upload_to=supplyr.core.models.Profile.get_gst_upload_path),
        ),
        migrations.AlterField(
            model_name='profile',
            name='operational_fields',
            field=models.ManyToManyField(blank=True, to='core.SubCategory'),
        ),
    ]

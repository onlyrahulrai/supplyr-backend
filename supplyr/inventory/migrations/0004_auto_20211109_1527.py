# Generated by Django 3.1.12 on 2021-11-09 09:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0003_auto_20211109_1525'),
    ]

    operations = [
        migrations.AlterField(
            model_name='variant',
            name='allow_inventory_tracking',
            field=models.BooleanField(default=False),
        ),
    ]

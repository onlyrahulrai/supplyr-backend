# Generated by Django 3.1.12 on 2022-09-28 08:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0019_auto_20220903_0124'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellerprofile',
            name='user_settings',
            field=models.JSONField(blank=True, default={}, null=True),
        ),
    ]

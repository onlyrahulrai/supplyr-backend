# Generated by Django 3.1.12 on 2023-03-19 05:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0023_auto_20230313_1203'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoicetemplate',
            name='is_public',
            field=models.BooleanField(default=True),
        ),
    ]

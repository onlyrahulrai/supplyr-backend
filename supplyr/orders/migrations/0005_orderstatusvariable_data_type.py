# Generated by Django 3.2.4 on 2021-12-17 18:11

from django.db import migrations
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_auto_20211217_1705'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderstatusvariable',
            name='data_type',
            field=django_mysql.models.EnumField(choices=[('text', 'Text'), ('date', 'Date'), ('integer', 'Integer'), ('decimal', 'Decimal')], default='text'),
        ),
    ]
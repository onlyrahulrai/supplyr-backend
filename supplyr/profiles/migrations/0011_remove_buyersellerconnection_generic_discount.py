# Generated by Django 3.1.12 on 2022-01-17 06:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0010_auto_20220108_1505'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='buyersellerconnection',
            name='generic_discount',
        ),
    ]

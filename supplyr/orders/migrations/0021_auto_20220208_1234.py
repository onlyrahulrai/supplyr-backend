# Generated by Django 3.1.12 on 2022-02-08 07:04

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0011_remove_buyersellerconnection_generic_discount'),
        ('orders', '0020_auto_20220208_1215'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='Transaction',
            new_name='Payment',
        ),
        migrations.RemoveField(
            model_name='ledger',
            name='updated_at',
        ),
    ]

# Generated by Django 3.1.12 on 2021-12-16 13:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0004_invoice'),
    ]

    operations = [
        migrations.AlterField(
            model_name='invoice',
            name='invoice_id',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]

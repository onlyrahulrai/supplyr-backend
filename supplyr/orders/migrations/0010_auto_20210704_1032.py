# Generated by Django 3.1.12 on 2021-07-04 05:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0009_auto_20210626_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
# Generated by Django 3.1.12 on 2021-08-05 08:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0005_auto_20210201_1203'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='sub_categories',
            field=models.ManyToManyField(related_name='products', to='inventory.Category'),
        ),
    ]

# Generated by Django 3.1.12 on 2021-06-26 10:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_sellerprofilereview'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellerprofilereview',
            name='comments',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]

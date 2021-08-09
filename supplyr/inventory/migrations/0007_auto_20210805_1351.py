# Generated by Django 3.1.12 on 2021-08-05 08:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0018_auto_20210805_1348'),
        ('inventory', '0006_auto_20210805_1348'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='subcategories', to='inventory.category'),
        ),
        migrations.AddField(
            model_name='category',
            name='seller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='profiles.sellerprofile'),
        ),
    ]
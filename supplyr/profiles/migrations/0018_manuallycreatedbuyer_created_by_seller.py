# Generated by Django 3.1.12 on 2022-08-13 10:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0017_auto_20220322_1355'),
    ]

    operations = [
        migrations.AddField(
            model_name='manuallycreatedbuyer',
            name='created_by_seller',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.RESTRICT, to='profiles.sellerprofile'),
        ),
    ]
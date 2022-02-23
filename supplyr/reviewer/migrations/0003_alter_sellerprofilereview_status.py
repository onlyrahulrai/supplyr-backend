# Generated by Django 3.2.4 on 2022-02-23 09:52

from django.db import migrations
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('reviewer', '0002_auto_20211023_1046'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellerprofilereview',
            name='status',
            field=django_mysql.models.EnumField(blank=True, choices=[('pending_approval', 'pending_approval'), ('profile_created', 'profile_created'), ('approved', 'approved'), ('rejected', 'rejected'), ('need_more_info', 'need_more_info'), ('permanently_rejected', 'permanently_rejected'), ('categories_selected', 'categories_selected')], default='profile_created', null=True),
        ),
    ]

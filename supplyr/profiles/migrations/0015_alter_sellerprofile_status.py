# Generated by Django 3.2.4 on 2022-02-23 09:47

from django.db import migrations
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('profiles', '0014_auto_20220221_0233'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sellerprofile',
            name='status',
            field=django_mysql.models.EnumField(blank=True, choices=[('pending_approval', 'Pending Approval'), ('profile_created', 'Profile Created'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('need_more_info', 'Need More Information'), ('permanently_rejected', 'Permanently Rejected'), ('categories_selected', 'Categories Selected')], default='profile_created', null=True),
        ),
    ]

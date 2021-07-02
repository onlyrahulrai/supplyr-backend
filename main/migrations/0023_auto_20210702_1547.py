# Generated by Django 3.1.12 on 2021-07-02 10:17

from django.db import migrations
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0022_auto_20210630_2022'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='sellerprofilereview',
            name='is_rejected',
        ),
        migrations.AddField(
            model_name='sellerprofilereview',
            name='status',
            field=django_mysql.models.EnumField(blank=True, choices=[('pending_approval', 'pending_approval'), ('approved', 'approved'), ('rejected', 'rejected'), ('need_more_info', 'need_more_info'), ('permanently_rejected', 'permanently_rejected'), ('new', 'new')], default='new', null=True),
        ),
    ]

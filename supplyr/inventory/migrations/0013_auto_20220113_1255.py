# Generated by Django 3.1.12 on 2022-01-13 07:25

from django.db import migrations, models
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0012_auto_20220113_1229'),
    ]

    operations = [
        migrations.AlterField(
            model_name='buyerdiscount',
            name='discount',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AlterField(
            model_name='buyerdiscount',
            name='discount_type',
            field=django_mysql.models.EnumField(choices=[('amount', 'Amount'), ('percentage', 'Percentage')], default='amount'),
        ),
    ]

# Generated by Django 3.1.12 on 2021-09-19 09:15

from django.db import migrations
import django_mysql.models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0015_autocategoryrule_is_active'),
    ]

    operations = [
        migrations.AlterField(
            model_name='autocategoryrule',
            name='comparison_type',
            field=django_mysql.models.EnumField(blank=True, choices=[('is_equal_to', 'Is equal to'), ('is_not_equal_to', 'Is not equal to'), ('starts_with', 'Starts With'), ('ends_with', 'Ends with'), ('contains', 'Contains'), ('does_not_contain', 'Does not contain'), ('is_greater_than', 'Is greater than'), ('is_less_than', 'Is less than')], null=True),
        ),
    ]

# Generated by Django 3.2.4 on 2022-02-10 19:50

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0014_remove_order_discount'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='item_note',
            field=models.TextField(blank=True, null=True),
        ),
    ]
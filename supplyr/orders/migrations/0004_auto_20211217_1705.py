# Generated by Django 3.2.4 on 2021-12-17 11:35

from django.db import migrations, models
import django.db.models.deletion
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0003_orderstatusvariable_orderstatusvariablevalue'),
    ]

    operations = [
        migrations.CreateModel(
            name='OrderStatusChoices',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=40)),
                ('slug', django_extensions.db.fields.AutoSlugField(blank=True, editable=False, max_length=40, populate_from=['name'], unique=True)),
                ('serial', models.IntegerField(blank=True, null=True)),
            ],
            options={
                'ordering': ('serial',),
            },
        ),
        migrations.AddField(
            model_name='orderstatusvariable',
            name='linked_order_status',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.RESTRICT, to='orders.orderstatuschoices'),
            preserve_default=False,
        ),
    ]

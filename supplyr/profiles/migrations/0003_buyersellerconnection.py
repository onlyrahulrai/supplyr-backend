# Generated by Django 3.1.2 on 2020-11-04 15:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0013_user_mobile_number'),
        ('profiles', '0002_auto_20201019_2213'),
    ]

    operations = [
        migrations.CreateModel(
            name='BuyerSellerConnection',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='connections', to='core.buyerprofile')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, related_name='connections', to='core.sellerprofile')),
            ],
            options={
                'verbose_name': 'BuyerSellerConnection',
                'verbose_name_plural': 'BuyerSellerConnections',
            },
        ),
    ]

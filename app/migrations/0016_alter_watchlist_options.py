# Generated by Django 3.2 on 2023-08-20 14:48

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0015_watchlist'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='watchlist',
            options={'verbose_name': 'Watchlist', 'verbose_name_plural': 'Watchlists'},
        ),
    ]

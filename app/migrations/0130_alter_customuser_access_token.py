# Generated by Django 4.2.7 on 2024-06-14 07:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0129_rename_token_watchlist_instrument_key_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_token',
            field=models.UUIDField(default='4ecede46ee534ffebfcfdfc46142871c', unique=True),
        ),
    ]

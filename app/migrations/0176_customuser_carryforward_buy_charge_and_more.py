# Generated by Django 4.2.7 on 2024-10-08 07:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0175_alter_watchlist_tag'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='carryforward_buy_charge',
            field=models.PositiveIntegerField(default=25),
        ),
        migrations.AddField(
            model_name='customuser',
            name='carryforward_sell_charge',
            field=models.PositiveIntegerField(default=25),
        ),
        migrations.AddField(
            model_name='customuser',
            name='intraday_buy_charge',
            field=models.PositiveIntegerField(default=24),
        ),
        migrations.AddField(
            model_name='customuser',
            name='intraday_sell_charge',
            field=models.PositiveIntegerField(default=24),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='margin',
            field=models.PositiveIntegerField(default=10),
        ),
    ]
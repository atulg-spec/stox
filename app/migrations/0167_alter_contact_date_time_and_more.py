# Generated by Django 5.0.3 on 2024-08-11 19:35

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0166_onstockbalancehistory_brokerage_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='contact',
            name='date_time',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='onstockbalancehistory',
            name='datefield',
            field=models.DateField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='order',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='position',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='position',
            name='last_traded_datetime',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name='shoonya_orders',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
        migrations.AlterField(
            model_name='transaction',
            name='datetime',
            field=models.DateTimeField(default=django.utils.timezone.now, null=True),
        ),
    ]
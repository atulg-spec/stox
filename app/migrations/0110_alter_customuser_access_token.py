# Generated by Django 4.2.5 on 2023-12-24 01:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0109_alter_customuser_access_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_token',
            field=models.UUIDField(default='8231216e738a4ed19646e0dcd017a7b7', unique=True),
        ),
    ]

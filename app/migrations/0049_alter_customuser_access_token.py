# Generated by Django 3.2 on 2023-09-20 10:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0048_auto_20230920_1606'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_token',
            field=models.UUIDField(default='a1bd0ac56f604b578e9aa61632ec525e', unique=True),
        ),
    ]

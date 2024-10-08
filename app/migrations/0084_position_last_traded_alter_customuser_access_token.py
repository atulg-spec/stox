# Generated by Django 4.2.5 on 2023-11-04 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0083_alter_customuser_access_token'),
    ]

    operations = [
        migrations.AddField(
            model_name='position',
            name='last_traded',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='customuser',
            name='access_token',
            field=models.UUIDField(default='f7da952d8cd44c8aa7e815397b0f69cd', unique=True),
        ),
    ]

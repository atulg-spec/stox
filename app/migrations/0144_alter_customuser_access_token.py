# Generated by Django 4.2.5 on 2024-07-07 17:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0143_alter_contact_options_alter_customuser_access_token'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='access_token',
            field=models.UUIDField(default='44b40c5669cb40f98087673bdf00f7ce', unique=True),
        ),
    ]
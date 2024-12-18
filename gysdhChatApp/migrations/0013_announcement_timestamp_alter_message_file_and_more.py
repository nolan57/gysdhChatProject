# Generated by Django 5.1.3 on 2024-11-15 16:21

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0012_user_date_joined_alter_user_email"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="timestamp",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="message",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="Message"),
        ),
        migrations.AlterField(
            model_name="message",
            name="timestamp",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]

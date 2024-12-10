# Generated by Django 5.1.3 on 2024-11-15 12:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0008_announcement_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="is_online",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="user",
            name="last_activity",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="Announcement"),
        ),
        migrations.AlterField(
            model_name="message",
            name="file",
            field=models.FileField(blank=True, null=True, upload_to="Message/"),
        ),
    ]

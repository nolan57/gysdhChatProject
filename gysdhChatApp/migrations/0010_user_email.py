# Generated by Django 5.1.3 on 2024-11-15 14:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0009_user_is_online_user_last_activity_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="email",
            field=models.EmailField(blank=True, max_length=255, null=True),
        ),
    ]

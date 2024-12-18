# Generated by Django 5.1.3 on 2024-11-15 16:08

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0011_update_user_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="date_joined",
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
        migrations.AlterField(
            model_name="user",
            name="email",
            field=models.EmailField(
                default="default@example.com", max_length=255, unique=True
            ),
        ),
    ]

# Generated by Django 4.2.16 on 2024-11-17 13:39

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0015_alter_message_options_message_reply_to_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="FileDownloadLog",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("file_name", models.CharField(max_length=255)),
                (
                    "file_type",
                    models.CharField(
                        choices=[("message", "消息文件"), ("announcement", "公告文件")],
                        max_length=50,
                    ),
                ),
                ("content_type", models.CharField(max_length=100)),
                ("file_size", models.BigIntegerField()),
                ("source_id", models.IntegerField()),
                ("downloaded_at", models.DateTimeField(auto_now_add=True)),
                ("ip_address", models.GenericIPAddressField(blank=True, null=True)),
                ("user_agent", models.TextField(blank=True, null=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="downloads",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "文件下载记录",
                "verbose_name_plural": "文件下载记录",
                "ordering": ["-downloaded_at"],
            },
        ),
    ]

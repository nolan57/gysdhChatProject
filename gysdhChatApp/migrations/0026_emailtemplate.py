# Generated by Django 5.1.3 on 2024-11-25 13:38

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0025_alter_systemsettings_chat_area_title_tag_usertag"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmailTemplate",
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
                (
                    "name",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="模板名称"
                    ),
                ),
                ("subject", models.CharField(max_length=200, verbose_name="邮件主题")),
                ("content", models.TextField(verbose_name="邮件内容")),
                ("description", models.TextField(blank=True, verbose_name="模板描述")),
                (
                    "variables",
                    models.JSONField(
                        default=dict,
                        help_text="以JSON格式存储可用于此模板的变量名及其描述",
                        verbose_name="可用变量",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="创建时间"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="更新时间"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_email_templates",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="创建者",
                    ),
                ),
            ],
            options={
                "verbose_name": "邮件模板",
                "verbose_name_plural": "邮件模板",
                "ordering": ["name"],
            },
        ),
    ]
# Generated by Django 5.1.3 on 2024-11-21 11:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0022_systemsettings_email_host_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="message",
            name="is_recalled",
            field=models.BooleanField(default=False, verbose_name="是否已撤回"),
        ),
        migrations.AddField(
            model_name="message",
            name="recalled_at",
            field=models.DateTimeField(blank=True, null=True, verbose_name="撤回时间"),
        ),
    ]

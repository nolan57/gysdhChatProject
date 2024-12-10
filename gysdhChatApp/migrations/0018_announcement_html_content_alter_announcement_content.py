# Generated by Django 4.2.16 on 2024-11-18 06:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("gysdhChatApp", "0017_usergroup_user_group"),
    ]

    operations = [
        migrations.AddField(
            model_name="announcement",
            name="html_content",
            field=models.TextField(blank=True, help_text="渲染后的HTML内容"),
        ),
        migrations.AlterField(
            model_name="announcement",
            name="content",
            field=models.TextField(help_text="支持富文本格式"),
        ),
    ]
# Generated by Django 5.1 on 2024-11-30 12:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gysdhChatApp', '0029_alter_announcement_options_announcement_expires_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='phone',
            field=models.CharField(blank=True, max_length=20, verbose_name='电话号码'),
        ),
    ]
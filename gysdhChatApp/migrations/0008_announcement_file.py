# Generated by Django 5.1.3 on 2024-11-12 17:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gysdhChatApp', '0007_message_file'),
    ]

    operations = [
        migrations.AddField(
            model_name='announcement',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='uploads/'),
        ),
    ]

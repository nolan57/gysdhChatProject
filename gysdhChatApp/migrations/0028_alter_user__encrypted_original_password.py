# Generated by Django 5.1 on 2024-11-26 23:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('gysdhChatApp', '0027_remove_user_original_password_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='_encrypted_original_password',
            field=models.TextField(default=''),
        ),
    ]

# Generated by Django 5.1 on 2024-11-30 14:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('conferenceApp', '0003_registration_conference_registration_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='conference',
            name='registration_form',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='conferences', to='conferenceApp.registrationform', verbose_name='当前报名表单'),
        ),
    ]

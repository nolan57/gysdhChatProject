from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('conferenceApp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='registrationform',
            name='formio_schema',
            field=models.JSONField(blank=True, null=True, verbose_name='Form.io Schema'),
        ),
        migrations.AddField(
            model_name='registrationform',
            name='is_formio',
            field=models.BooleanField(default=False, verbose_name='是否使用 Form.io'),
        ),
    ]

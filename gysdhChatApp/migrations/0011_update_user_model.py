from django.db import migrations, models
import gysdhChatApp.models

def update_existing_users(apps, schema_editor):
    User = apps.get_model('gysdhChatApp', 'User')
    for i, user in enumerate(User.objects.all()):
        if not user.email:
            user.email = f"user{i}@example.com"
        if not hasattr(user, 'original_password'):
            user.original_password = 'password123'
        user.save()

class Migration(migrations.Migration):

    dependencies = [
        ('gysdhChatApp', '0010_user_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='original_password',
            field=models.CharField(default='password123', max_length=100),
        ),
        migrations.RunPython(update_existing_users),
        migrations.AlterField(
            model_name='user',
            name='email',
            field=models.EmailField(max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='number',
            field=models.CharField(default=gysdhChatApp.models.generate_unique_number, editable=False, max_length=6, unique=True),
        ),
    ]

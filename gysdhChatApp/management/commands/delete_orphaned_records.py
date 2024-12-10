from django.core.management.base import BaseCommand
from gysdhChatApp.models import Message

class Command(BaseCommand):
    help = 'Delete orphaned records in the Message model'

    def handle(self, *args, **kwargs):
        orphaned_messages = Message.objects.filter(sender__isnull=True) | Message.objects.filter(recipient__isnull=True)

        if orphaned_messages.exists():
            orphaned_messages.delete()
            self.stdout.write(self.style.SUCCESS('Orphaned messages deleted successfully.'))
        else:
            self.stdout.write(self.style.SUCCESS('No orphaned messages found.'))

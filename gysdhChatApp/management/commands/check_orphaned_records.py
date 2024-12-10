from django.core.management.base import BaseCommand
from gysdhChatApp.models import Announcement, Message, User

class Command(BaseCommand):
    help = 'Check for orphaned records in Announcement and Message models'

    def handle(self, *args, **kwargs):
        orphaned_announcements = Announcement.objects.filter(publisher__isnull=True)
        orphaned_messages = Message.objects.filter(sender__isnull=True) | Message.objects.filter(recipient__isnull=True)

        if orphaned_announcements.exists():
            self.stdout.write(self.style.ERROR('Orphaned announcements found:'))
            for announcement in orphaned_announcements:
                self.stdout.write(f'Announcement ID: {announcement.id}, Content: {announcement.content}')

        if orphaned_messages.exists():
            self.stdout.write(self.style.ERROR('Orphaned messages found:'))
            for message in orphaned_messages:
                self.stdout.write(f'Message ID: {message.id}, Content: {message.content}')

        if not orphaned_announcements.exists() and not orphaned_messages.exists():
            self.stdout.write(self.style.SUCCESS('No orphaned records found.'))

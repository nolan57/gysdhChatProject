from django.core.management.base import BaseCommand
from django.utils import timezone
from ...services.reminder_service import ReminderService

class Command(BaseCommand):
    help = '发送问卷提醒'

    def handle(self, *args, **kwargs):
        self.stdout.write(f'开始发送问卷提醒 - {timezone.now()}')
        
        try:
            ReminderService.send_reminders()
            self.stdout.write(self.style.SUCCESS('问卷提醒发送完成！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'发送问卷提醒时出错: {str(e)}'))

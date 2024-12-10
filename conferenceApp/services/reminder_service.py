from datetime import datetime, timedelta
from django.utils import timezone
from django.core.mail import send_mail
from django.template import Template, Context
from django.conf import settings
from ..models.survey import SurveyReminder, ReminderLog
from ..models.participant import Participant

class ReminderService:
    @staticmethod
    def get_due_reminders():
        """获取需要发送的提醒"""
        now = timezone.now()
        current_time = now.time()
        
        # 获取所有活动的提醒
        active_reminders = SurveyReminder.objects.filter(
            is_active=True,
            start_date__lte=now.date(),
            end_date__gte=now.date(),
        )
        
        due_reminders = []
        for reminder in active_reminders:
            # 检查是否到达发送时间
            if reminder.time <= current_time:
                # 根据频率检查是否需要发送
                if ReminderService._should_send_reminder(reminder):
                    due_reminders.append(reminder)
        
        return due_reminders
    
    @staticmethod
    def _should_send_reminder(reminder):
        """检查是否应该发送提醒"""
        if not reminder.last_sent:
            return True
            
        now = timezone.now()
        last_sent = reminder.last_sent
        
        if reminder.frequency == 'once':
            return False  # 单次提醒且已发送
        elif reminder.frequency == 'daily':
            return last_sent.date() < now.date()
        elif reminder.frequency == 'weekly':
            return (now - last_sent).days >= 7
        elif reminder.frequency == 'monthly':
            # 简单处理，可能需要更复杂的月份计算
            return (now - last_sent).days >= 30
        
        return False
    
    @staticmethod
    def get_target_participants(reminder):
        """获取提醒目标参与者"""
        survey = reminder.survey
        if reminder.target_participants == SurveyReminder.INCOMPLETE_ONLY:
            # 获取未完成问卷的参与者
            completed_users = survey.responses.values_list('user_id', flat=True)
            return Participant.objects.filter(
                conference=survey.conference
            ).exclude(user_id__in=completed_users)
        else:
            # 获取所有参与者
            return Participant.objects.filter(conference=survey.conference)
    
    @staticmethod
    def send_reminders():
        """发送所有到期的提醒"""
        due_reminders = ReminderService.get_due_reminders()
        
        for reminder in due_reminders:
            participants = ReminderService.get_target_participants(reminder)
            
            for participant in participants:
                if reminder.email_reminder:
                    ReminderService.send_email_reminder(reminder, participant)
                
                if reminder.sms_reminder:
                    ReminderService.send_sms_reminder(reminder, participant)
            
            # 更新最后发送时间
            reminder.last_sent = timezone.now()
            reminder.save()
    
    @staticmethod
    def send_email_reminder(reminder, participant):
        """发送邮件提醒"""
        try:
            # 渲染邮件内容
            context = Context({
                'participant': participant,
                'survey': reminder.survey,
                'conference': reminder.survey.conference,
            })
            
            subject = Template(reminder.email_subject_template).render(context)
            body = Template(reminder.email_body_template).render(context)
            
            # 发送邮件
            send_mail(
                subject,
                body,
                settings.DEFAULT_FROM_EMAIL,
                [participant.user.email],
                fail_silently=False,
            )
            
            # 记录日志
            ReminderLog.objects.create(
                reminder=reminder,
                participant=participant,
                type='email',
                status='success'
            )
            
        except Exception as e:
            # 记录错误日志
            ReminderLog.objects.create(
                reminder=reminder,
                participant=participant,
                type='email',
                status='failed',
                error_message=str(e)
            )
    
    @staticmethod
    def send_sms_reminder(reminder, participant):
        """发送短信提醒"""
        try:
            # 渲染短信内容
            context = Context({
                'participant': participant,
                'survey': reminder.survey,
                'conference': reminder.survey.conference,
            })
            
            message = Template(reminder.sms_template).render(context)
            
            # TODO: 集成短信发送服务
            # 这里需要集成具体的短信服务商API
            # sms_service.send_sms(participant.phone, message)
            
            # 记录日志
            ReminderLog.objects.create(
                reminder=reminder,
                participant=participant,
                type='sms',
                status='success'
            )
            
        except Exception as e:
            # 记录错误日志
            ReminderLog.objects.create(
                reminder=reminder,
                participant=participant,
                type='sms',
                status='failed',
                error_message=str(e)
            )

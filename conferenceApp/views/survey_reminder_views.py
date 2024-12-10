from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils import timezone
from django.urls import reverse

from ..models.survey import Survey, SurveyReminder, ReminderLog
from ..services.reminder_service import ReminderService

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_list(request, survey_id):
    """提醒列表"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    reminders = survey.reminders.all()
    
    # 分页
    paginator = Paginator(reminders, 10)
    page = request.GET.get('page')
    reminders = paginator.get_page(page)
    
    return render(request, 'conferenceApp/survey/reminder_list.html', {
        'survey': survey,
        'reminders': reminders
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_create(request, survey_id):
    """创建提醒"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    
    if request.method == 'POST':
        # 处理表单提交
        name = request.POST.get('name')
        description = request.POST.get('description')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        frequency = request.POST.get('frequency')
        time = request.POST.get('time')
        email_reminder = request.POST.get('email_reminder') == 'on'
        sms_reminder = request.POST.get('sms_reminder') == 'on'
        target_participants = request.POST.get('target_participants')
        email_subject_template = request.POST.get('email_subject_template')
        email_body_template = request.POST.get('email_body_template')
        sms_template = request.POST.get('sms_template')
        
        reminder = SurveyReminder.objects.create(
            survey=survey,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            time=time,
            email_reminder=email_reminder,
            sms_reminder=sms_reminder,
            target_participants=target_participants,
            email_subject_template=email_subject_template,
            email_body_template=email_body_template,
            sms_template=sms_template
        )
        
        messages.success(request, '提醒创建成功！')
        return redirect('conference:reminder_list', survey_id=survey.id)
    
    return render(request, 'conferenceApp/survey/reminder_create.html', {
        'survey': survey
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_edit(request, reminder_id):
    """编辑提醒"""
    reminder = get_object_or_404(SurveyReminder, id=reminder_id, survey__created_by=request.user)
    
    if request.method == 'POST':
        # 处理表单提交
        reminder.name = request.POST.get('name')
        reminder.description = request.POST.get('description')
        reminder.start_date = request.POST.get('start_date')
        reminder.end_date = request.POST.get('end_date')
        reminder.frequency = request.POST.get('frequency')
        reminder.time = request.POST.get('time')
        reminder.email_reminder = request.POST.get('email_reminder') == 'on'
        reminder.sms_reminder = request.POST.get('sms_reminder') == 'on'
        reminder.target_participants = request.POST.get('target_participants')
        reminder.email_subject_template = request.POST.get('email_subject_template')
        reminder.email_body_template = request.POST.get('email_body_template')
        reminder.sms_template = request.POST.get('sms_template')
        reminder.save()
        
        messages.success(request, '提醒更新成功！')
        return redirect('conference:reminder_list', survey_id=reminder.survey.id)
    
    return render(request, 'conferenceApp/survey/reminder_edit.html', {
        'reminder': reminder
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_delete(request, reminder_id):
    """删除提醒"""
    reminder = get_object_or_404(SurveyReminder, id=reminder_id, survey__created_by=request.user)
    survey_id = reminder.survey.id
    reminder.delete()
    
    messages.success(request, '提醒已删除！')
    return redirect('conference:reminder_list', survey_id=survey_id)

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_toggle(request, reminder_id):
    """启用/禁用提醒"""
    reminder = get_object_or_404(SurveyReminder, id=reminder_id, survey__created_by=request.user)
    reminder.is_active = not reminder.is_active
    reminder.save()
    
    return JsonResponse({
        'status': 'success',
        'is_active': reminder.is_active
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_logs(request, reminder_id):
    """查看提醒日志"""
    reminder = get_object_or_404(SurveyReminder, id=reminder_id, survey__created_by=request.user)
    logs = reminder.logs.all().order_by('-sent_at')
    
    # 分页
    paginator = Paginator(logs, 20)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    
    return render(request, 'conferenceApp/survey/reminder_logs.html', {
        'reminder': reminder,
        'logs': logs
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def reminder_preview(request, reminder_id):
    """预览提醒内容"""
    reminder = get_object_or_404(SurveyReminder, id=reminder_id, survey__created_by=request.user)
    
    # 获取一个示例参与者
    participant = reminder.survey.conference.participants.first()
    
    if participant:
        try:
            from django.template import Template, Context
            context = Context({
                'participant': participant,
                'survey': reminder.survey,
                'conference': reminder.survey.conference,
            })
            
            email_subject = Template(reminder.email_subject_template).render(context)
            email_body = Template(reminder.email_body_template).render(context)
            sms_content = Template(reminder.sms_template).render(context)
            
            return JsonResponse({
                'status': 'success',
                'email_subject': email_subject,
                'email_body': email_body,
                'sms_content': sms_content
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': str(e)
            })
    else:
        return JsonResponse({
            'status': 'error',
            'message': '没有找到参与者来预览内容'
        })

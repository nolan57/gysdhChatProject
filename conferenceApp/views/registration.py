from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone
from django.db import transaction
from django.conf import settings
from ..models import (
    Conference, RegistrationForm, FormField, FieldOption,
    Registration, Participant, SupplierCompany, ContactPerson
)

@login_required
def manage_registration_form(request, conference_id):
    """管理会议报名表单"""
    conference = get_object_or_404(Conference, pk=conference_id)
    registration_form = RegistrationForm.objects.filter(conference=conference).first()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create_form':
            # 创建新表单
            registration_form = RegistrationForm.objects.create(
                conference=conference,
                title=request.POST.get('title'),
                description=request.POST.get('description'),
                max_participants=request.POST.get('max_participants', 1)
            )
            messages.success(request, '报名表单创建成功')
        
        elif action == 'add_field':
            # 添加表单字段
            field = FormField.objects.create(
                form=registration_form,
                label=request.POST.get('label'),
                field_type=request.POST.get('field_type'),
                required=request.POST.get('required', False),
                order=request.POST.get('order', 0)
            )
            # 如果是选择类型字段，添加选项
            if field.field_type in ['select', 'radio', 'checkbox']:
                options = request.POST.getlist('options[]')
                for option in options:
                    FieldOption.objects.create(field=field, value=option)
            messages.success(request, '字段添加成功')
        
        elif action == 'update_form':
            # 更新表单设置
            registration_form.title = request.POST.get('title')
            registration_form.description = request.POST.get('description')
            registration_form.max_participants = request.POST.get('max_participants', 1)
            registration_form.save()
            messages.success(request, '表单更新成功')
        
        elif action == 'delete_field':
            field_id = request.POST.get('field_id')
            FormField.objects.filter(id=field_id).delete()
            messages.success(request, '字段删除成功')
        
        return redirect('manage_registration_form', conference_id=conference_id)
    
    context = {
        'conference': conference,
        'registration_form': registration_form,
        'field_types': FormField.FIELD_TYPES
    }
    return render(request, 'conferenceApp/registration/manage_form.html', context)

@login_required
def notify_suppliers(request, conference_id):
    """发送报名通知给供应商联系人"""
    conference = get_object_or_404(Conference, pk=conference_id)
    if request.method == 'POST':
        companies = SupplierCompany.objects.filter(
            id__in=request.POST.getlist('companies')
        )
        
        for company in companies:
            contacts = ContactPerson.objects.filter(company=company)
            for contact in contacts:
                # 生成报名链接
                registration_url = request.build_absolute_uri(
                    f'/conference/{conference.id}/register/'
                )
                
                # 准备邮件内容
                context = {
                    'contact': contact,
                    'conference': conference,
                    'registration_url': registration_url
                }
                email_html = render_to_string(
                    'conferenceApp/emails/registration_invitation.html',
                    context
                )
                email_text = render_to_string(
                    'conferenceApp/emails/registration_invitation.txt',
                    context
                )
                
                # 发送邮件
                send_mail(
                    subject=f'{conference.name} - 会议报名通知',
                    message=email_text,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[contact.email],
                    html_message=email_html
                )
        
        messages.success(request, '报名通知已发送')
        return redirect('conference_detail', pk=conference_id)
    
    context = {
        'conference': conference,
        'companies': SupplierCompany.objects.all()
    }
    return render(request, 'conferenceApp/registration/notify_suppliers.html', context)

@login_required
def submit_registration(request, conference_id):
    """提交会议报名"""
    conference = get_object_or_404(Conference, pk=conference_id)
    registration_form = get_object_or_404(RegistrationForm, conference=conference)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                # 创建或更新参会者信息
                participant_data = {
                    'name': request.POST.get('name'),
                    'company': request.user.contactperson.company,
                    'position': request.POST.get('position'),
                    'phone': request.POST.get('phone'),
                    'email': request.POST.get('email')
                }
                participant, created = Participant.objects.update_or_create(
                    registration_number=request.POST.get('registration_number', None),
                    defaults=participant_data
                )
                
                # 创建报名记录
                registration = Registration.objects.create(
                    conference=conference,
                    participant=participant,
                    form=registration_form,
                    submitted_by=request.user,
                    status='pending'
                )
                
                # 保存表单字段答案
                for field in registration_form.fields.all():
                    value = request.POST.get(f'field_{field.id}')
                    if field.field_type == 'checkbox':
                        value = ','.join(request.POST.getlist(f'field_{field.id}'))
                    registration.answers.create(field=field, value=value)
                
                messages.success(request, '报名提交成功，请等待审核')
                return redirect('registration_confirmation', registration_id=registration.id)
                
        except Exception as e:
            messages.error(request, f'报名提交失败：{str(e)}')
            return redirect('submit_registration', conference_id=conference_id)
    
    context = {
        'conference': conference,
        'registration_form': registration_form
    }
    return render(request, 'conferenceApp/registration/submit_form.html', context)

@login_required
def registration_confirmation(request, registration_id):
    """报名确认页面"""
    registration = get_object_or_404(Registration, pk=registration_id)
    context = {
        'registration': registration
    }
    return render(request, 'conferenceApp/registration/confirmation.html', context)

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import transaction

from ..models.conference import Conference
from ..models.registration import Registration, RegistrationForm
from ..models.participant import Participant
from ..models.company import ContactPerson

@login_required
def conference_register(request, pk):
    """会议报名视图"""
    conference = get_object_or_404(Conference, pk=pk)
    
    # 检查会议是否有指定的报名表单
    if not conference.registration_form:
        messages.error(request, '该会议尚未设置报名表单，请联系管理员')
        return redirect('conference:detail', pk=pk)
    
    # 获取当前用户的联系人信息
    contact_person = get_object_or_404(ContactPerson, user=request.user)
    
    # 获取或创建报名记录
    registration = Registration.objects.filter(
        conference=conference,
        contact_person=contact_person
    ).first()
    
    if request.method == 'POST':
        # 处理表单提交
        form_data = request.POST.dict()
        form_data.pop('csrfmiddlewaretoken', None)
        
        try:
            with transaction.atomic():
                if registration:
                    # 更新现有报名
                    registration.data = form_data
                    registration.save()
                    messages.success(request, '报名信息已更新')
                else:
                    # 创建新报名
                    registration = Registration.objects.create(
                        conference=conference,
                        contact_person=contact_person,
                        form=conference.registration_form,  # 使用会议指定的表单
                        data=form_data
                    )
                    messages.success(request, '报名成功')
                
                return redirect('conference:company_registration_manage', conference_id=pk)
        except Exception as e:
            messages.error(request, f'报名失败：{str(e)}')
    
    # 准备表单上下文
    context = {
        'conference': conference,
        'form': conference.registration_form,  # 使用会议指定的表单
        'registration': registration,
        'contact_person': contact_person,
        'is_edit': bool(registration),
    }
    
    return render(request, 'conferenceApp/registration/submit_form.html', context)

@login_required
def registration_list(request, conference_id):
    """会议报名列表视图"""
    conference = get_object_or_404(Conference, id=conference_id)
    
    # 只有主办方联系人可以查看报名列表
    if not request.user.is_staff and request.user.email != conference.contact_email:
        messages.error(request, '您没有权限查看报名列表')
        return redirect('conference:detail', pk=conference_id)
    
    registrations = conference.registrations.all().select_related(
        'participant', 'contact_person'
    ).order_by('-submitted_at')
    
    context = {
        'conference': conference,
        'registrations': registrations,
    }
    return render(request, 'conferenceApp/registration_list.html', context)

@login_required
def registration_approve(request, registration_id):
    """审核报名"""
    registration = get_object_or_404(Registration, id=registration_id)
    conference = registration.conference
    
    # 检查权限
    if not request.user.is_staff and request.user.email != conference.contact_email:
        messages.error(request, '您没有权限审核报名')
        return redirect('conference:registration_list', conference_id=conference.id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            registration.status = 'confirmed'
            messages.success(request, '已确认报名')
        elif action == 'reject':
            registration.status = 'rejected'
            messages.success(request, '已拒绝报名')
        
        registration.save()
    
    return redirect('conference:registration_list', conference_id=conference.id)

@login_required
def registration_cancel(request, registration_id):
    """取消报名"""
    registration = get_object_or_404(Registration, id=registration_id)
    conference = registration.conference
    
    # 检查权限
    if not (request.user == registration.participant.user or 
            request.user.is_staff or 
            request.user.email == conference.contact_email):
        messages.error(request, '您没有权限取消此报名')
        return redirect('conference:detail', pk=conference.id)
    
    if request.method == 'POST':
        registration.status = 'cancelled'
        registration.save()
        messages.success(request, '报名已取消')
    
    return redirect('conference:detail', pk=conference.id)

@login_required
def company_registration_manage(request, conference_id):
    """管理公司参会人员视图"""
    conference = get_object_or_404(Conference, id=conference_id)
    
    # 检查会议是否可以报名
    if not conference.status == 'registration':
        messages.error(request, '该会议当前不在报名期间')
        return redirect('conference:detail', pk=conference_id)
    
    # 获取当前公司的所有报名记录
    company_registrations = Registration.objects.filter(
        conference=conference,
        participant__company__code=request.user.companyCode,
        status__in=['pending', 'confirmed']
    ).select_related('participant')
    
    # 计算剩余可报名人数
    current_count = company_registrations.count()
    spaces_left = conference.company_max_participants - current_count
    
    context = {
        'conference': conference,
        'registrations': company_registrations,
        'spaces_left': spaces_left,
        'company_max_participants': conference.company_max_participants,
    }
    
    return render(request, 'conferenceApp/registration/company_participants.html', context)

@login_required
def add_participant(request, conference_id):
    """添加参会人员"""
    conference = get_object_or_404(Conference, id=conference_id)
    
    if request.method == 'POST':
        # 检查公司报名人数限制
        current_count = Registration.objects.filter(
            conference=conference,
            participant__company__code=request.user.companyCode,
            status__in=['pending', 'confirmed']
        ).count()
        
        if current_count >= conference.company_max_participants:
            messages.error(request, '已达到公司报名人数上限')
            return redirect('conference:company_registration_manage', conference_id=conference_id)
        
        try:
            with transaction.atomic():
                # 创建参会人员记录
                participant = Participant.objects.create(
                    company=request.user.company,
                    registered_by=request.user.contact_person,
                    name=request.POST.get('name'),
                    position=request.POST.get('position'),
                    phone=request.POST.get('phone'),
                    email=request.POST.get('email')
                )
                
                # 创建报名记录
                registration = Registration.objects.create(
                    conference=conference,
                    participant=participant,
                    status='pending'
                )
                
                messages.success(request, '参会人员添加成功')
                return redirect('conference:company_registration_manage', conference_id=conference_id)
                
        except Exception as e:
            messages.error(request, f'添加参会人员失败：{str(e)}')
            return redirect('conference:company_registration_manage', conference_id=conference_id)
    
    # GET 请求显示添加表单
    context = {
        'conference': conference
    }
    return render(request, 'conferenceApp/registration/submit_form.html', context)

@login_required
def remove_participant(request, registration_id):
    """移除参会人员"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # 检查是否是同一公司的用户
    if registration.participant.company.code != request.user.companyCode:
        messages.error(request, '无权操作其他公司的报名记录')
        return redirect('conference:company_registration_manage', conference_id=registration.conference.id)
    
    try:
        with transaction.atomic():
            # 删除参会人员和报名记录
            participant = registration.participant
            registration.delete()
            participant.delete()
            
            messages.success(request, '参会人员移除成功')
    except Exception as e:
        messages.error(request, f'移除参会人员失败：{str(e)}')
    
    return redirect('conference:company_registration_manage', conference_id=registration.conference.id)

@login_required
def edit_participant(request, registration_id):
    """编辑参会人员信息"""
    registration = get_object_or_404(Registration, id=registration_id)
    
    # 检查是否是同一公司的用户
    if registration.participant.company.code != request.user.companyCode:
        messages.error(request, '无权操作其他公司的报名记录')
        return redirect('conference:company_registration_manage', conference_id=registration.conference.id)
    
    if request.method == 'POST':
        try:
            with transaction.atomic():
                participant = registration.participant
                participant.name = request.POST.get('name')
                participant.position = request.POST.get('position')
                participant.phone = request.POST.get('phone')
                participant.email = request.POST.get('email')
                participant.save()
                
                messages.success(request, '参会人员信息更新成功')
                return redirect('conference:company_registration_manage', conference_id=registration.conference.id)
                
        except Exception as e:
            messages.error(request, f'更新参会人员信息失败：{str(e)}')
            return redirect('conference:company_registration_manage', conference_id=registration.conference.id)
    
    # GET 请求显示编辑表单
    context = {
        'conference': registration.conference,
        'registration': registration,
        'participant': registration.participant
    }
    return render(request, 'conferenceApp/registration/edit_participant.html', context)

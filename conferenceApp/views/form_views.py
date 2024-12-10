from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_http_methods, require_POST
from django.db import transaction
import json
from django.core.exceptions import ValidationError

from ..models import Conference, RegistrationForm, FieldLogicRule

@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_form(request):
    """报名表单管理视图"""
    # 获取所有表单和会议
    registration_forms = RegistrationForm.objects.all().order_by('-created_at')
    conferences = Conference.objects.all().order_by('-created_at')
    
    context = {
        'title': '报名表单管理',
        'subtitle': '管理会议报名表单和字段设置',
        'registration_forms': registration_forms,
        'conferences': conferences,
    }
    return render(request, 'conferenceApp/registration/manage_form.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def set_current_form(request):
    """设置会议当前使用的报名表单"""
    if request.method != 'POST':
        return HttpResponseForbidden()
        
    form_id = request.POST.get('form_id')
    conference_id = request.POST.get('conference_id')
    
    if not form_id or not conference_id:
        messages.error(request, '请选择表单和会议')
        return redirect('conference:manage_form')
    
    try:
        with transaction.atomic():
            form = get_object_or_404(RegistrationForm, id=form_id)
            conference = get_object_or_404(Conference, id=conference_id)
            
            # 更新会议的当前表单
            conference.registration_form = form
            conference.save()
            
            messages.success(request, f'已将表单 {form.name} 设置为会议 {conference.name} 的报名表单')
            return redirect('conference:manage_form')
            
    except Exception as e:
        messages.error(request, f'设置失败：{str(e)}')
        return redirect('conference:manage_form')

@login_required
@user_passes_test(lambda u: u.is_staff)
def formio_builder(request):
    """Form.io 表单构建器视图"""
    context = {
        'title': 'Form.io 表单构建器',
        'subtitle': '使用 Form.io 创建和管理报名表单',
        'conferences': Conference.objects.all().order_by('-created_at'),
    }
    return render(request, 'conferenceApp/registration/formio_builder.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
def manage_formio(request):
    """Form.io 表单管理视图"""
    forms = RegistrationForm.objects.filter(is_formio=True).order_by('-created_at')
    
    context = {
        'forms': forms,
    }
    return render(request, 'conferenceApp/registration/manage_formio.html', context)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def delete_formio(request):
    """批量删除 Form.io 表单"""
    try:
        data = json.loads(request.body)
        form_ids = data.get('form_ids', [])
        
        # 检查表单是否正在被使用
        in_use_forms = []
        for form_id in form_ids:
            form = get_object_or_404(RegistrationForm, id=form_id)
            if Conference.objects.filter(registration_form=form).exists():
                in_use_forms.append(form.name)
        
        if in_use_forms:
            return JsonResponse({
                'success': False,
                'error': f'以下表单正在被会议使用，无法删除：{", ".join(in_use_forms)}'
            })
        
        # 删除表单
        RegistrationForm.objects.filter(id__in=form_ids).delete()
        
        return JsonResponse({
            'success': True,
            'message': '删除成功'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
def render_formio(request, conference_id):
    """渲染 Form.io 表单"""
    conference = get_object_or_404(Conference, id=conference_id)
    
    # 获取会议关联的表单
    form = conference.registration_form
    if not form:
        return JsonResponse({'error': '会议没有关联的表单'}, status=404)
    
    if not form.is_formio:
        return JsonResponse({'error': '此表单不是 Form.io 表单'}, status=400)
    
    # 获取表单的逻辑规则
    logic_rules = form.logic_rules.filter(is_active=True).order_by('priority')
    rules_data = [{
        'triggerField': rule.trigger_field.name,
        'operator': rule.operator,
        'value': rule.value,
        'targetField': rule.target_field.name,
        'action': rule.action
    } for rule in logic_rules]
    
    context = {
        'conference': conference,
        'form': form,
        'logic_rules': json.dumps(rules_data)
    }
    return render(request, 'conferenceApp/registration/formio_form.html', context)

@require_POST
@login_required
def submit_formio(request, conference_id):
    """提交 Form.io 表单"""
    try:
        # 获取会议和表单
        conference = get_object_or_404(Conference, pk=conference_id)
        form = conference.registration_form
        if not form or not form.is_formio:
            return JsonResponse({'error': '表单不存在或类型不正确'}, status=400)
        
        # 获取用户公司
        company = request.user.company
        if not company:
            return JsonResponse({'error': '用户未关联公司'}, status=400)
        
        # 获取表单数据
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({'error': '无效的表单数据'}, status=400)
        
        # 保存表单提交
        try:
            submission = form.save_formio_submission(
                user=request.user,
                company=company,
                data=data
            )
            return JsonResponse({
                'success': True,
                'message': '提交成功',
                'submission_id': submission.id,
                'redirect_url': reverse('conference:detail', args=[conference.id])
            })
        except ValidationError as e:
            return JsonResponse({'error': str(e)}, status=400)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@require_POST
@login_required
@user_passes_test(lambda u: u.is_staff)
def create_registration_form(request):
    """创建 Form.io 表单"""
    try:
        data = json.loads(request.body)
        name = data.get('name')
        conference_id = data.get('conference_id')
        schema = data.get('schema')
        logic_rules = data.get('logic_rules', [])
        
        if not name or not schema:
            return JsonResponse({'error': '表单名称和配置不能为空'}, status=400)
        
        with transaction.atomic():
            # 创建表单
            form = RegistrationForm.objects.create(
                name=name,
                is_formio=True,
                formio_schema=schema
            )
            
            # 如果指定了会议，关联表单
            if conference_id:
                conference = get_object_or_404(Conference, id=conference_id)
                conference.registration_form = form
                conference.save()
            
            # 创建逻辑规则
            for rule in logic_rules:
                FieldLogicRule.objects.create(
                    form=form,
                    trigger_field=rule['triggerField'],
                    operator=rule['operator'],
                    value=rule['value'],
                    target_field=rule['targetField'],
                    action=rule['action']
                )
            
            return JsonResponse({
                'success': True,
                'form_id': form.id,
                'message': '表单创建成功'
            })
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

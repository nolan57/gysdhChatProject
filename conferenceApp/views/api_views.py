from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
import json
from django.db import transaction

from ..models import (
    RegistrationForm, FormField, FieldOption, FieldLogicRule,
    Conference
)

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from ..models import Registration #, Tag, Group
from gysdhChatApp.models import Tag, UserGroup

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def get_registration_form(request, form_id):
    """获取报名表单详情"""
    form = get_object_or_404(RegistrationForm, id=form_id)
    
    # 构建表单数据
    form_data = {
        'id': form.id,
        'name': form.name,
        'description': form.description,
        'is_active': form.is_active,
        'start_time': form.start_time.isoformat() if form.start_time else None,
        'end_time': form.end_time.isoformat() if form.end_time else None,
        'fields': []
    }
    
    # 获取表单字段
    for field in form.fields.all():
        field_data = {
            'id': field.id,
            'field_type': field.field_type,
            'label': field.label,
            'name': field.name,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'required': field.required,
            'order': field.order,
            'validation_regex': field.validation_regex,
            'error_message': field.error_message,
            'default_value': field.default_value,
            'is_unique_in_company': field.is_unique_in_company,
            'max_occurrences': field.max_occurrences,
            'options': []
        }
        
        # 获取字段选项
        if field.field_type in ['select', 'radio', 'checkbox']:
            for option in field.options.all():
                option_data = {
                    'id': option.id,
                    'label': option.label,
                    'value': option.value,
                    'order': option.order,
                    'is_exclusive': option.is_exclusive,
                    'max_selections': option.max_selections
                }
                field_data['options'].append(option_data)
        
        form_data['fields'].append(field_data)
    
    return JsonResponse(form_data)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def create_registration_form(request):
    """创建新的报名表单"""
    try:
        data = json.loads(request.body)
        
        # 创建表单
        form = RegistrationForm.objects.create(
            name=data['name'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True),
            start_time=data.get('start_time'),
            end_time=data.get('end_time')
        )
        
        # 如果指定了会议，关联会议
        if data.get('conference_id'):
            conference = get_object_or_404(Conference, id=data['conference_id'])
            conference.registration_form = form
            # 如果没有指定时间，使用会议时间
            if not data.get('start_time') and not data.get('end_time'):
                form.start_time = conference.start_time
                form.end_time = conference.end_time
                form.save()
            conference.save()
        
        # 创建表单字段
        for field_data in data.get('fields', []):
            field = FormField.objects.create(
                form=form,
                field_type=field_data['field_type'],
                label=field_data['label'],
                name=field_data['name'],
                placeholder=field_data.get('placeholder'),
                help_text=field_data.get('help_text'),
                required=field_data.get('required', True),
                order=field_data['order'],
                validation_regex=field_data.get('validation_regex'),
                error_message=field_data.get('error_message'),
                default_value=field_data.get('default_value'),
                is_unique_in_company=field_data.get('is_unique_in_company', False),
                max_occurrences=field_data.get('max_occurrences')
            )
            
            # 创建字段选项
            if field.field_type in ['select', 'radio', 'checkbox']:
                for option_data in field_data.get('options', []):
                    FieldOption.objects.create(
                        field=field,
                        label=option_data['label'],
                        value=option_data['value'],
                        order=option_data['order'],
                        is_exclusive=option_data.get('is_exclusive', False),
                        max_selections=option_data.get('max_selections')
                    )
        
        return JsonResponse({'id': form.id, 'message': '创建成功'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["PUT"])
def update_registration_form(request, form_id):
    """更新报名表单"""
    try:
        form = get_object_or_404(RegistrationForm, id=form_id)
        data = json.loads(request.body)
        
        # 更新表单基本信息
        form.name = data['name']
        form.description = data.get('description', '')
        form.is_active = data.get('is_active', True)
        form.start_time = data.get('start_time', form.start_time)
        form.end_time = data.get('end_time', form.end_time)
        form.save()
        
        # 更新会议关联
        if data.get('conference_id'):
            conference = get_object_or_404(Conference, id=data['conference_id'])
            conference.registration_form = form
            # 如果没有指定时间，使用会议时间
            if not data.get('start_time') and not data.get('end_time'):
                form.start_time = conference.start_time
                form.end_time = conference.end_time
                form.save()
            conference.save()
        
        # 更新表单字段
        if 'fields' in data:
            # 删除旧字段
            form.fields.all().delete()
            
            # 创建新字段
            for field_data in data['fields']:
                field = FormField.objects.create(
                    form=form,
                    field_type=field_data['field_type'],
                    label=field_data['label'],
                    name=field_data['name'],
                    placeholder=field_data.get('placeholder'),
                    help_text=field_data.get('help_text'),
                    required=field_data.get('required', True),
                    order=field_data['order'],
                    validation_regex=field_data.get('validation_regex'),
                    error_message=field_data.get('error_message'),
                    default_value=field_data.get('default_value'),
                    is_unique_in_company=field_data.get('is_unique_in_company', False),
                    max_occurrences=field_data.get('max_occurrences')
                )
                
                # 创建字段选项
                if field.field_type in ['select', 'radio', 'checkbox']:
                    for option_data in field_data.get('options', []):
                        FieldOption.objects.create(
                            field=field,
                            label=option_data['label'],
                            value=option_data['value'],
                            order=option_data['order'],
                            is_exclusive=option_data.get('is_exclusive', False),
                            max_selections=option_data.get('max_selections')
                        )
        
        return JsonResponse({'message': '更新成功'})
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["DELETE"])
def delete_registration_form(request, form_id):
    """删除报名表单"""
    try:
        form = get_object_or_404(RegistrationForm, id=form_id)
        form.delete()
        return JsonResponse({'message': '删除成功'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def preview_registration_form(request, form_id):
    """预览报名表单"""
    form = get_object_or_404(RegistrationForm, id=form_id)
    
    # 构建预览数据
    preview_data = {
        'id': form.id,
        'name': form.name,
        'description': form.description,
        'fields': []
    }
    
    # 获取表单字段
    for field in form.fields.all():
        field_data = {
            'type': field.field_type,
            'label': field.label,
            'name': field.name,
            'placeholder': field.placeholder,
            'help_text': field.help_text,
            'required': field.required,
            'validation_regex': field.validation_regex,
            'error_message': field.error_message,
            'default_value': field.default_value,
            'options': []
        }
        
        # 获取字段选项
        if field.field_type in ['select', 'radio', 'checkbox']:
            field_data['options'] = list(field.options.values('label', 'value', 'order'))
        
        preview_data['fields'].append(field_data)
    
    return JsonResponse(preview_data)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def get_field_logic_rules(request, form_id, field_id):
    """获取字段的逻辑规则"""
    try:
        field = get_object_or_404(FormField, id=field_id, form_id=form_id)
        rules = field.logic_rules.all().select_related('target_field')
        
        rules_data = []
        for rule in rules:
            rule_data = {
                'id': rule.id,
                'target_field': {
                    'id': rule.target_field.id,
                    'label': rule.target_field.label,
                    'field_type': rule.target_field.field_type,
                    'options': [
                        {'value': opt.value, 'label': opt.label}
                        for opt in rule.target_field.options.all()
                    ] if rule.target_field.field_type in ['select', 'radio', 'checkbox'] else []
                },
                'operator': rule.operator,
                'value': rule.value,
                'action': rule.action,
                'action_value': rule.action_value
            }
            rules_data.append(rule_data)
        
        return JsonResponse({
            'success': True,
            'rules': rules_data,
            'available_fields': [
                {
                    'id': f.id,
                    'label': f.label,
                    'field_type': f.field_type,
                    'options': [
                        {'value': opt.value, 'label': opt.label}
                        for opt in f.options.all()
                    ] if f.field_type in ['select', 'radio', 'checkbox'] else []
                }
                for f in FormField.objects.filter(form_id=form_id).exclude(id=field_id)
            ]
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["POST"])
def save_field_logic_rules(request, form_id, field_id):
    """保存字段的逻辑规则"""
    try:
        field = get_object_or_404(FormField, id=field_id, form_id=form_id)
        rules_data = json.loads(request.body)
        
        # 开启数据库事务
        with transaction.atomic():
            # 删除现有规则
            field.logic_rules.all().delete()
            
            # 批量创建新规则
            new_rules = []
            validation_errors = []
            
            for rule_data in rules_data:
                try:
                    rule = FieldLogicRule(
                        source_field=field,
                        target_field_id=rule_data['target_field_id'],
                        operator=rule_data['operator'],
                        value=rule_data['value'],
                        action=rule_data['action'],
                        action_value=rule_data.get('action_value', '')
                    )
                    # 验证规则
                    rule.clean()
                    rule.validate_conflicts()
                    new_rules.append(rule)
                except ValidationError as e:
                    validation_errors.append({
                        'target_field_id': rule_data['target_field_id'],
                        'error': str(e)
                    })
            
            # 如果有验证错误，返回错误信息
            if validation_errors:
                return JsonResponse({
                    'success': False,
                    'errors': validation_errors
                }, status=400)
            
            # 批量保存规则
            FieldLogicRule.objects.bulk_create(new_rules)
        
        return JsonResponse({
            'success': True,
            'message': '逻辑规则保存成功',
            'rules_count': len(new_rules)
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'保存失败：{str(e)}'
        }, status=500)

@login_required
@user_passes_test(lambda u: u.is_staff)
@require_http_methods(["GET"])
def preview_field_logic_rules(request, form_id, field_id):
    """预览字段的逻辑规则效果"""
    try:
        field = get_object_or_404(FormField, id=field_id, form_id=form_id)
        rules = field.logic_rules.all().select_related('target_field')
        
        # 生成规则预览数据
        preview_data = []
        for rule in rules:
            target_field = rule.target_field
            condition_desc = {
                'equals': f'等于 "{rule.value}"',
                'not_equals': f'不等于 "{rule.value}"',
                'contains': f'包含 "{rule.value}"',
                'not_contains': f'不包含 "{rule.value}"',
                'greater_than': f'大于 {rule.value}',
                'less_than': f'小于 {rule.value}',
                'in': f'在列表 [{rule.value}] 中',
                'not_in': f'不在列表 [{rule.value}] 中',
                'starts_with': f'以 "{rule.value}" 开头',
                'ends_with': f'以 "{rule.value}" 结尾',
                'is_empty': '为空',
                'is_not_empty': '不为空',
                'between': f'在范围 {rule.value} 内'
            }.get(rule.operator, rule.operator)
            
            action_desc = {
                'show': '显示',
                'hide': '隐藏',
                'enable': '启用',
                'disable': '禁用',
                'require': '必填',
                'unrequire': '非必填',
                'set_value': f'设置值为 "{rule.action_value}"',
                'clear_value': '清除值'
            }.get(rule.action, rule.action)
            
            preview_data.append({
                'id': rule.id,
                'description': f'当 {field.label} {condition_desc} 时，{action_desc} {target_field.label}',
                'source_field': {
                    'id': field.id,
                    'label': field.label,
                    'field_type': field.field_type
                },
                'target_field': {
                    'id': target_field.id,
                    'label': target_field.label,
                    'field_type': target_field.field_type
                },
                'condition': condition_desc,
                'action': action_desc
            })
        
        return JsonResponse({
            'success': True,
            'preview': preview_data
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_tags_to_participants(request):
    participant_ids = request.data.get('participant_ids', [])
    tag_id = request.data.get('tag_id')
    tag = get_object_or_404(Tag, id=tag_id)

    for participant_id in participant_ids:
        participant = get_object_or_404(Registration, id=participant_id)
        participant.tags.add(tag)

    return Response({'success': True, 'message': 'Tags assigned successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def assign_group_to_participants(request):
    participant_ids = request.data.get('participant_ids', [])
    group_id = request.data.get('group_id')
    group = get_object_or_404(UserGroup, id=group_id)

    for participant_id in participant_ids:
        participant = get_object_or_404(Registration, id=participant_id)
        participant.groups.add(group)

    return Response({'success': True, 'message': 'Group assigned successfully.'})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def batch_delete_participants(request, conference_id):
    """Batch delete participants from a conference"""
    participant_ids = request.data.get('participant_ids', [])
    if not participant_ids:
        return Response({'error': 'No participants selected'}, status=400)
    
    try:
        # Get the conference and verify it exists
        conference = get_object_or_404(Conference, id=conference_id)
        
        # Delete the selected registrations
        deleted_count = Registration.objects.filter(
            id__in=participant_ids,
            conference=conference
        ).delete()[0]
        
        return Response({
            'message': f'Successfully deleted {deleted_count} participants',
            'deleted_count': deleted_count
        })
    except Exception as e:
        return Response({'error': str(e)}, status=500)

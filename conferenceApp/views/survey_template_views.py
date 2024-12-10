from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.core.paginator import Paginator

from ..models.survey_template import SurveyTemplate
from ..models.survey import Survey

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_list(request):
    """模板列表视图"""
    # 获取公开的模板和用户自己创建的模板
    templates = SurveyTemplate.objects.filter(
        models.Q(is_public=True) | models.Q(created_by=request.user)
    ).order_by('-created_at')
    
    # 分页
    paginator = Paginator(templates, 12)
    page = request.GET.get('page')
    templates = paginator.get_page(page)
    
    return render(request, 'conferenceApp/survey/template_list.html', {
        'templates': templates
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_create(request):
    """创建模板视图"""
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            formio_schema = request.POST.get('formio_schema')
            
            with transaction.atomic():
                template = SurveyTemplate.objects.create(
                    title=data.get('title'),
                    description=data.get('description'),
                    category=data.get('category'),
                    formio_schema=formio_schema,
                    is_public=data.get('is_public') == 'on',
                    created_by=request.user
                )
                
                messages.success(request, '模板创建成功！')
                return redirect('conference:template_list')
                
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
            
    return render(request, 'conferenceApp/survey/template_create.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_edit(request, template_id):
    """编辑模板视图"""
    template = get_object_or_404(SurveyTemplate, id=template_id)
    
    # 检查权限
    if not template.is_public and template.created_by != request.user:
        messages.error(request, '您没有权限编辑此模板！')
        return redirect('conference:template_list')
    
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            formio_schema = request.POST.get('formio_schema')
            
            with transaction.atomic():
                template.title = data.get('title')
                template.description = data.get('description')
                template.category = data.get('category')
                template.formio_schema = formio_schema
                template.is_public = data.get('is_public') == 'on'
                template.save()
                
                messages.success(request, '模板更新成功！')
                return redirect('conference:template_list')
                
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    return render(request, 'conferenceApp/survey/template_edit.html', {
        'template': template
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def template_delete(request, template_id):
    """删除模板"""
    template = get_object_or_404(SurveyTemplate, id=template_id)
    
    # 检查权限
    if template.created_by != request.user:
        messages.error(request, '您没有权限删除此模板！')
        return redirect('conference:template_list')
    
    if request.method == 'POST':
        try:
            template.delete()
            messages.success(request, '模板已删除！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('conference:template_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def create_survey_from_template(request, template_id):
    """从模板创建问卷"""
    template = get_object_or_404(SurveyTemplate, id=template_id)
    
    # 检查权限
    if not template.is_public and template.created_by != request.user:
        messages.error(request, '您没有权限使用此模板！')
        return redirect('conference:template_list')
    
    try:
        with transaction.atomic():
            survey = Survey.objects.create(
                title=f'{template.title} - 副本',
                description=template.description,
                formio_schema=template.formio_schema,
                created_by=request.user
            )
            
            messages.success(request, '问卷创建成功！')
            return redirect('conference:survey_edit', survey.id)
            
    except Exception as e:
        messages.error(request, f'创建失败：{str(e)}')
        return redirect('conference:template_list')

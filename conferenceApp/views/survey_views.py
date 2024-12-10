from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.urls import reverse

from ..models.survey import Survey, SurveyResponse, SurveyConference
from ..models.conference import Conference

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_list(request):
    """问卷列表视图"""
    surveys = Survey.objects.filter(created_by=request.user).order_by('-created_at')
    
    # 分页
    paginator = Paginator(surveys, 10)
    page = request.GET.get('page')
    surveys = paginator.get_page(page)
    
    return render(request, 'conferenceApp/survey/list.html', {
        'surveys': surveys
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_create(request):
    """创建问卷视图"""
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            formio_schema = request.POST.get('formio_schema')
            
            with transaction.atomic():
                survey = Survey.objects.create(
                    title=data.get('title'),
                    description=data.get('description'),
                    formio_schema=formio_schema,
                    created_by=request.user
                )
                
                messages.success(request, '问卷创建成功！')
                return redirect('conference:survey_edit', survey.id)
                
        except Exception as e:
            messages.error(request, f'创建失败：{str(e)}')
            
    return render(request, 'conferenceApp/survey/create.html')

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_edit(request, survey_id):
    """编辑问卷视图"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            formio_schema = request.POST.get('formio_schema')
            
            with transaction.atomic():
                survey.title = data.get('title')
                survey.description = data.get('description')
                survey.formio_schema = formio_schema
                survey.save()
                
                messages.success(request, '问卷更新成功！')
                return redirect('conference:survey_list')
                
        except Exception as e:
            messages.error(request, f'更新失败：{str(e)}')
    
    return render(request, 'conferenceApp/survey/edit.html', {
        'survey': survey
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_delete(request, survey_id):
    """删除问卷"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    
    if request.method == 'POST':
        try:
            survey.delete()
            messages.success(request, '问卷已删除！')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
    
    return redirect('conference:survey_list')

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_publish(request, survey_id):
    """发布问卷"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    
    if request.method == 'POST':
        try:
            data = request.POST.dict()
            
            with transaction.atomic():
                survey.status = 'published'
                survey.start_time = data.get('start_time')
                survey.end_time = data.get('end_time')
                survey.save()
                
                # 关联会议
                conference_ids = request.POST.getlist('conference_ids')
                required_ids = request.POST.getlist('required_ids')
                
                # 清除旧的关联
                survey.surveyconference_set.all().delete()
                
                # 创建新的关联
                for conf_id in conference_ids:
                    SurveyConference.objects.create(
                        survey=survey,
                        conference_id=conf_id,
                        is_required=conf_id in required_ids
                    )
                
                messages.success(request, '问卷已发布！')
                return redirect('conference:survey_list')
                
        except Exception as e:
            messages.error(request, f'发布失败：{str(e)}')
    
    # 获取可选的会议列表
    conferences = Conference.objects.filter(
        status__in=['published', 'registration', 'in_progress']
    ).order_by('-start_date')
    
    return render(request, 'conferenceApp/survey/publish.html', {
        'survey': survey,
        'conferences': conferences
    })

@login_required
def survey_fill(request, survey_id, conference_id):
    """填写问卷"""
    survey = get_object_or_404(Survey, id=survey_id)
    conference = get_object_or_404(Conference, id=conference_id)
    
    # 检查用户是否有权限填写
    if not survey.can_submit(request.user):
        messages.error(request, '您没有权限填写此问卷或问卷已关闭！')
        return redirect('conference:detail', conference_id)
    
    if request.method == 'POST':
        try:
            response_data = request.POST.get('response_data')
            
            # 创建或更新回答
            SurveyResponse.objects.update_or_create(
                survey=survey,
                user=request.user,
                conference=conference,
                defaults={'response_data': response_data}
            )
            
            messages.success(request, '问卷提交成功！')
            return redirect('conference:detail', conference_id)
            
        except Exception as e:
            messages.error(request, f'提交失败：{str(e)}')
    
    # 检查是否已经提交过
    existing_response = SurveyResponse.objects.filter(
        survey=survey,
        user=request.user,
        conference=conference
    ).first()
    
    return render(request, 'conferenceApp/survey/fill.html', {
        'survey': survey,
        'conference': conference,
        'existing_response': existing_response
    })

@login_required
@user_passes_test(lambda u: u.is_staff)
def survey_responses(request, survey_id):
    """查看问卷回答"""
    survey = get_object_or_404(Survey, id=survey_id, created_by=request.user)
    responses = survey.responses.all().select_related('user', 'conference')
    
    # 分页
    paginator = Paginator(responses, 20)
    page = request.GET.get('page')
    responses = paginator.get_page(page)
    
    return render(request, 'conferenceApp/survey/responses.html', {
        'survey': survey,
        'responses': responses
    })

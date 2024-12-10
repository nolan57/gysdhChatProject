from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Count
from ..models import Tag, UserTag, User
from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def tag_list(request):
    """标签列表页面"""
    tags = Tag.objects.annotate(user_count=Count('tagged_users')).order_by('name')
    
    # 分页
    paginator = Paginator(tags, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'tag/tag_list.html', {
        'page_obj': page_obj,
        'is_paginated': paginator.num_pages > 1,
        'paginator': paginator
    })

@staff_member_required
def create_tag(request):
    """创建新标签"""
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color', '#3B82F6')
        description = request.POST.get('description', '')
        
        if Tag.objects.filter(name=name).exists():
            messages.error(request, f'标签 "{name}" 已存在')
            return redirect('tag_list')
        
        tag = Tag.objects.create(
            name=name,
            color=color,
            description=description,
            created_by=request.user
        )
        messages.success(request, f'标签 "{tag.name}" 创建成功')
        return redirect('tag_list')
    
    return render(request, 'tag/create_tag.html')

@staff_member_required
def update_tag(request, tag_id):
    """更新标签"""
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        color = request.POST.get('color')
        description = request.POST.get('description')
        
        if Tag.objects.filter(name=name).exclude(id=tag_id).exists():
            messages.error(request, f'标签 "{name}" 已存在')
            return redirect('update_tag', tag_id=tag_id)
        
        tag.name = name
        tag.color = color
        tag.description = description
        tag.save()
        
        messages.success(request, f'标签 "{tag.name}" 更新成功')
        return redirect('tag_list')
    
    return render(request, 'tag/update_tag.html', {'tag': tag})

@staff_member_required
def delete_tag(request, tag_id):
    """删除标签"""
    tag = get_object_or_404(Tag, id=tag_id)
    
    if request.method == 'POST':
        name = tag.name
        tag.delete()
        messages.success(request, f'标签 "{name}" 已删除')
        return redirect('tag_list')
    
    return render(request, 'tag/delete_tag.html', {'tag': tag})

@staff_member_required
def manage_user_tags(request, user_id):
    """管理用户标签"""
    user = get_object_or_404(User, id=user_id)
    all_tags = Tag.objects.all().order_by('name')
    user_tags = set(user.user_tags.values_list('tag_id', flat=True))
    
    if request.method == 'POST':
        # 获取提交的标签ID列表
        new_tags = set(map(int, request.POST.getlist('tags')))
        
        # 要添加的标签
        tags_to_add = new_tags - user_tags
        # 要删除的标签
        tags_to_remove = user_tags - new_tags
        
        # 添加新标签
        for tag_id in tags_to_add:
            UserTag.objects.create(
                user=user,
                tag_id=tag_id,
                added_by=request.user
            )
        
        # 删除旧标签
        UserTag.objects.filter(user=user, tag_id__in=tags_to_remove).delete()
        
        messages.success(request, f'用户 "{user.name}" 的标签已更新')
        return redirect('user_detail', user_id=user_id)
    
    return render(request, 'tag/manage_user_tags.html', {
        'user': user,
        'all_tags': all_tags,
        'user_tags': user_tags
    })

@staff_member_required
def ajax_add_user_tag(request):
    """通过AJAX添加用户标签"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        tag_id = request.POST.get('tag_id')
        
        try:
            user = User.objects.get(id=user_id)
            tag = Tag.objects.get(id=tag_id)
            
            # 检查标签是否已存在
            if not UserTag.objects.filter(user=user, tag=tag).exists():
                UserTag.objects.create(
                    user=user,
                    tag=tag,
                    added_by=request.user
                )
                return JsonResponse({
                    'status': 'success',
                    'message': f'标签 "{tag.name}" 已添加到用户 "{user.name}"'
                })
            return JsonResponse({
                'status': 'error',
                'message': '该标签已添加到此用户'
            })
        except (User.DoesNotExist, Tag.DoesNotExist):
            return JsonResponse({
                'status': 'error',
                'message': '用户或标签不存在'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': '无效的请求方法'
    })

@staff_member_required
def ajax_remove_user_tag(request):
    """通过AJAX移除用户标签"""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        tag_id = request.POST.get('tag_id')
        
        try:
            user_tag = UserTag.objects.get(
                user_id=user_id,
                tag_id=tag_id
            )
            tag_name = user_tag.tag.name
            user_name = user_tag.user.name
            user_tag.delete()
            
            return JsonResponse({
                'status': 'success',
                'message': f'已从用户 "{user_name}" 移除标签 "{tag_name}"'
            })
        except UserTag.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': '未找到指定的用户标签'
            })
    
    return JsonResponse({
        'status': 'error',
        'message': '无效的请求方法'
    })

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, FileResponse, Http404
from .models import User, SystemSettings, Message, Announcement, FileDownloadLog
import json
import os
import mimetypes
from django.core.mail import send_mail
from django.contrib.admin.views.decorators import staff_member_required

@login_required
def user_management(request):
    if not request.user.is_admin:
        messages.error(request, '您没有权限访问此页面')
        return redirect('home')
    
    users = User.objects.all().order_by('-date_joined')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            try:
                name = request.POST.get('name')
                company_code = request.POST.get('companyCode')
                email = request.POST.get('email')
                password = request.POST.get('password')
                
                if not all([name, company_code, email]):
                    raise ValueError('所有字段都是必填的')
                
                User.objects.create_user(
                    name=name,
                    companyCode=company_code,
                    email=email,
                    password=password
                )
                messages.success(request, '用户创建成功')
            except Exception as e:
                messages.error(request, f'创建用户失败: {str(e)}')
        
        elif action == 'edit':
            try:
                user_id = request.POST.get('user_id')
                user = User.objects.get(id=user_id)
                
                user.name = request.POST.get('name', user.name)
                user.companyCode = request.POST.get('companyCode', user.companyCode)
                user.email = request.POST.get('email', user.email)
                
                new_password = request.POST.get('password')
                if new_password:
                    user.set_password(new_password)
                    user.original_password = new_password
                
                user.can_publish_announcements = request.POST.get('can_publish_announcements') == 'on'
                user.can_private_message = request.POST.get('can_private_message') == 'on'
                user.is_event_staff = request.POST.get('is_event_staff') == 'on'
                
                user.save()
                messages.success(request, '用户信息更新成功')
            except User.DoesNotExist:
                messages.error(request, '用户不存在')
            except Exception as e:
                messages.error(request, f'更新用户失败: {str(e)}')
        
        elif action == 'delete':
            try:
                user_id = request.POST.get('user_id')
                user = User.objects.get(id=user_id)
                if user.is_admin:
                    messages.error(request, '不能删除管理员用户')
                else:
                    user.delete()
                    messages.success(request, '用户删除成功')
            except User.DoesNotExist:
                messages.error(request, '用户不存在')
            except Exception as e:
                messages.error(request, f'删除用户失败: {str(e)}')
    
    return render(request, 'admin/user_management.html', {'users': users})

@login_required
def system_management(request):
    if not request.user.is_admin:
        messages.error(request, '您没有权限访问此页面')
        return redirect('index')
    
    settings = SystemSettings.objects.first()
    if not settings:
        settings = SystemSettings.objects.create()
    
    # 获取邮箱设置
    email_settings = {
        'email_host_user': os.environ.get('EMAIL_HOST_USER', ''),
        'email_host_password': os.environ.get('EMAIL_HOST_PASSWORD', '')
    }
    
    context = {
        'settings': settings,
        'email_settings': email_settings
    }
    
    return render(request, 'system_management.html', context)

@login_required
def update_system_settings(request):
    if not request.user.is_admin:
        messages.error(request, '您没有权限执行此操作')
        return redirect('home')
    
    if request.method == 'POST':
        settings = SystemSettings.objects.first()
        if not settings:
            settings = SystemSettings.objects.create()
        
        settings.chat_title = request.POST.get('chat_title', settings.chat_title)
        settings.chat_area_title = request.POST.get('chat_area_title', settings.chat_area_title)
        settings.updated_by = request.user
        settings.save()
        messages.success(request, '系统设置已更新')
    
    return redirect('system_management')

@login_required
@staff_member_required
def update_email_settings(request):
    if request.method == 'POST':
        email_host_user = request.POST.get('email_host_user')
        email_host_password = request.POST.get('email_host_password')
        
        # 更新.env文件
        env_path = os.path.join(settings.BASE_DIR, '.env')
        env_lines = []
        
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                env_lines = f.readlines()
        
        # 更新或添加邮箱设置
        email_user_found = False
        email_pass_found = False
        
        for i, line in enumerate(env_lines):
            if line.startswith('EMAIL_HOST_USER='):
                env_lines[i] = f'EMAIL_HOST_USER={email_host_user}\n'
                email_user_found = True
            elif line.startswith('EMAIL_HOST_PASSWORD='):
                env_lines[i] = f'EMAIL_HOST_PASSWORD={email_host_password}\n'
                email_pass_found = True
        
        if not email_user_found:
            env_lines.append(f'EMAIL_HOST_USER={email_host_user}\n')
        if not email_pass_found:
            env_lines.append(f'EMAIL_HOST_PASSWORD={email_host_password}\n')
        
        with open(env_path, 'w') as f:
            f.writelines(env_lines)
        
        # 更新环境变量
        os.environ['EMAIL_HOST_USER'] = email_host_user
        os.environ['EMAIL_HOST_PASSWORD'] = email_host_password
        
        messages.success(request, '邮箱设置已更新')
        return redirect('system_management')
    
    return redirect('system_management')

@login_required
@staff_member_required
def send_test_email(request):
    if request.method == 'POST':
        try:
            send_mail(
                'GYSDH Chat 测试邮件',
                '这是一封测试邮件，用于验证邮箱配置是否正确。\n\n如果您收到这封邮件，说明邮箱配置成功！',
                settings.EMAIL_HOST_USER,
                [settings.EMAIL_HOST_USER],
                fail_silently=False,
            )
            return JsonResponse({'status': 'success', 'message': '测试邮件已发送，请检查收件箱'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'发送失败：{str(e)}'})
    
    return JsonResponse({'status': 'error', 'message': '不支持的请求方法'})

@login_required
def download_file(request, file_type, file_id):
    try:
        # 获取文件对象
        if file_type == 'message':
            file_obj = get_object_or_404(Message, id=file_id)
            file_path = file_obj.file.path
            source_id = file_obj.id
        elif file_type == 'announcement':
            file_obj = get_object_or_404(Announcement, id=file_id)
            file_path = file_obj.file.path
            source_id = file_obj.id
        else:
            raise Http404("不支持的文件类型")

        # 检查文件是否存在
        if not os.path.exists(file_path):
            raise Http404("文件不存在")

        # 获取文件信息
        file_name = os.path.basename(file_path)
        content_type, _ = mimetypes.guess_type(file_path)
        if not content_type:
            content_type = 'application/octet-stream'

        # 记录下载信息
        FileDownloadLog.objects.create(
            user=request.user,
            file_name=file_name,
            file_type=file_type,
            content_type=content_type,
            file_size=os.path.getsize(file_path),
            source_id=source_id,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

        # 返回文件
        response = FileResponse(open(file_path, 'rb'), content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{file_name}"'
        return response

    except Exception as e:
        messages.error(request, f'文件下载失败: {str(e)}')
        return redirect('home')

@login_required
@staff_member_required
def download_logs(request):
    if not request.user.is_admin:
        messages.error(request, '您没有权限访问此页面')
        return redirect('home')
    
    logs = FileDownloadLog.objects.select_related('user').order_by('-downloaded_at')
    return render(request, 'admin/download_logs.html', {'logs': logs})

@login_required
def delete_announcement(request, announcement_id):
    if not request.user.can_publish_announcements:
        return JsonResponse({'success': False, 'error': '您没有权限删除公告'})
    
    try:
        announcement = get_object_or_404(Announcement, id=announcement_id)
        announcement.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def batch_delete_announcements(request):
    if not request.user.can_publish_announcements:
        return JsonResponse({'success': False, 'error': '您没有权限删除公告'})
    
    try:
        data = json.loads(request.body)
        announcement_ids = data.get('announcement_ids', [])
        
        if not announcement_ids:
            return JsonResponse({'success': False, 'error': '未选择任何公告'})
        
        Announcement.objects.filter(id__in=announcement_ids).delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

from django.views.generic import TemplateView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import ListView
from django.http import HttpResponse, HttpResponseForbidden
from django.utils import timezone
from ..models import Notice, FileDownloadLog, Announcement, SystemSettings
from ..services.export_service import ExportService
from datetime import date

class SystemManagementView(LoginRequiredMixin, View):
    template_name = 'system_management.html'  # 使用根目录下的模板

    def get(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限访问此页面')
            return redirect('chat_view', user_id=request.user.id)
        settings = SystemSettings.get_settings()
        return render(request, self.template_name, {
            'today': date.today(),
            'settings': settings,
            'email_settings': settings,  # 为了保持向后兼容，同时传递email_settings
        })

class UpdateSystemSettingsView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限修改系统设置')
            return redirect('system_management')
        
        settings = SystemSettings.get_settings()
        settings.chat_title = request.POST.get('chat_title', settings.chat_title)
        settings.chat_area_title = request.POST.get('chat_area_title', settings.chat_area_title)
        settings.updated_by = request.user
        settings.save()
        
        messages.success(request, '系统设置更新成功')
        return redirect('system_management')

class PublishNoticeView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限发布注意事项')
            return redirect('system_management')
        
        current_notice = Notice.objects.filter(is_active=True).first()
        return render(request, 'publish_notice.html', {'current_notice': current_notice})

    def post(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限发布注意事项')
            return redirect('system_management')
        
        content = request.POST.get('notice_content')  # 修改为匹配模板中的字段名
        if content:
            # 将之前的所有注意事项设为非激活
            Notice.objects.filter(is_active=True).update(is_active=False)
            
            # 创建新的注意事项
            Notice.objects.create(
                content=content,
                publisher=request.user,
                is_active=True
            )
            messages.success(request, '注意事项发布成功')
        else:
            messages.error(request, '注意事项内容不能为空')
        
        return redirect('system_management')

class FileDownloadLogView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = FileDownloadLog
    template_name = 'download_logs.html'
    context_object_name = 'logs'
    paginate_by = 50
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_queryset(self):
        queryset = FileDownloadLog.objects.select_related('user')
        
        # 获取过滤参数
        username = self.request.GET.get('username', '').strip()
        file_name = self.request.GET.get('file_name', '').strip()
        file_type = self.request.GET.get('file_type', '').strip()
        date_from = self.request.GET.get('date_from', '').strip()
        date_to = self.request.GET.get('date_to', '').strip()
        ip_address = self.request.GET.get('ip_address', '').strip()
        
        # 应用筛选条件
        if username:
            queryset = queryset.filter(user__name__icontains=username)
        if file_name:
            queryset = queryset.filter(file_name__icontains=file_name)
        if file_type:
            queryset = queryset.filter(file_type=file_type)  # 文件类型使用精确匹配
        if date_from:
            queryset = queryset.filter(downloaded_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(downloaded_at__date__lte=date_to)
        if ip_address:
            queryset = queryset.filter(ip_address__icontains=ip_address)
            
        return queryset.order_by('-downloaded_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 获取所有文件类型供筛选使用
        context['file_types'] = FileDownloadLog.objects.values_list(
            'file_type', flat=True
        ).distinct().exclude(file_type='').order_by('file_type')
        # 保存当前的筛选条件
        context['filters'] = {
            'username': self.request.GET.get('username', ''),
            'file_name': self.request.GET.get('file_name', ''),
            'file_type': self.request.GET.get('file_type', ''),
            'date_from': self.request.GET.get('date_from', ''),
            'date_to': self.request.GET.get('date_to', ''),
            'ip_address': self.request.GET.get('ip_address', ''),
        }
        return context

class ExportView(LoginRequiredMixin, View):
    def get(self, request):
        if not request.user.is_admin:
            return HttpResponseForbidden("没有导出权限")
        
        export_service = ExportService()
        file = export_service.export_file_download_log()
        response = HttpResponse(file, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = 'attachment; filename="file_download_log.xlsx"'
        return response

class UpdateEmailSettingsView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限修改邮件设置')
            return redirect('chat_view', user_id=request.user.id)
        
        settings = SystemSettings.get_settings()
        settings.email_host = request.POST.get('email_host', '')
        settings.email_port = int(request.POST.get('email_port', 587))
        settings.email_host_user = request.POST.get('email_host_user', '')
        settings.email_host_password = request.POST.get('email_host_password', '')
        settings.email_use_tls = request.POST.get('email_use_tls') == 'on'
        settings.updated_by = request.user
        settings.save()
        
        # 更新Django邮件设置
        from django.conf import settings as django_settings
        django_settings.EMAIL_HOST = settings.email_host
        django_settings.EMAIL_PORT = settings.email_port
        django_settings.EMAIL_HOST_USER = settings.email_host_user
        django_settings.EMAIL_HOST_PASSWORD = settings.email_host_password
        django_settings.EMAIL_USE_TLS = settings.email_use_tls
        
        messages.success(request, '邮件设置已更新')
        return redirect('system_management')

class SendTestEmailView(LoginRequiredMixin, View):
    def post(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限发送测试邮件')
            return redirect('chat_view', user_id=request.user.id)
        
        test_email = request.POST.get('test_email')
        if not test_email:
            messages.error(request, '请输入测试邮箱地址')
            return redirect('system_management')
        
        try:
            from django.core.mail import send_mail
            send_mail(
                '测试邮件',
                '这是一封测试邮件，用于验证邮件服务器配置是否正确。',
                None,  # 使用 settings.py 中配置的 DEFAULT_FROM_EMAIL
                [test_email],
                fail_silently=False,
            )
            messages.success(request, '测试邮件已发送')
        except Exception as e:
            messages.error(request, f'发送测试邮件失败：{str(e)}')
        
        return redirect('system_management')

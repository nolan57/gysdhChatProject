from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect
from ..models import Notice, Announcement
from ..mixins import AdminRequiredMixin
from ..services.cache_service import CacheService
from django.views import View
from django.shortcuts import render
from django.http import JsonResponse
import os
import uuid
from django.conf import settings
from ..services.security_service import SecurityService
import logging
import magic
from django.utils.dateparse import parse_datetime
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import HttpResponse
import json
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)

class QuickPublishNoticeView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    """快速发布注意事项视图"""
    model = Notice
    fields = ['content']
    template_name = 'notice/quick_publish.html'
    success_url = reverse_lazy('conference:dashboard')
    
    def form_valid(self, form):
        """设置发布者为当前用户"""
        form.instance.publisher = self.request.user
        response = super().form_valid(form)
        
        # 清除所有其他注意事项的激活状态
        Notice.objects.exclude(pk=form.instance.pk).update(is_active=False)
        
        messages.success(self.request, '注意事项发布成功！')
        return response
    
    def form_invalid(self, form):
        """表单验证失败时的处理"""
        messages.error(self.request, '注意事项发布失败，请检查输入！')
        return super().form_invalid(form)


class QuickPublishAnnouncementView(AdminRequiredMixin, View):
    template_name = 'notice/quick_publish_announcement.html'

    def get(self, request):
        # 获取所有公告，按置顶和创建时间排序
        announcements = Announcement.objects.all().order_by('-is_sticky', '-timestamp')
        
        context = {
            'priority_choices': Announcement.PRIORITY_CHOICES,
            'announcements': announcements
        }
        return render(request, self.template_name, context)

    def post(self, request):
        try:
            content = request.POST.get('content', '').strip()
            if not content:
                return JsonResponse({
                    'success': False,
                    'message': '公告内容不能为空！'
                })

            # 获取其他字段
            priority = int(request.POST.get('priority', 1))
            expires_at = request.POST.get('expires_at')
            is_sticky = request.POST.get('is_sticky') == 'true'

            # 清理和验证HTML内容
            cleaned_content = SecurityService.sanitize_html(content)
            
            # 确保内容不是纯HTML标签
            if not cleaned_content or cleaned_content.isspace():
                return JsonResponse({
                    'success': False,
                    'message': '公告内容不能为空！'
                })

            # 解析过期时间
            expires_at_datetime = None
            if expires_at:
                expires_at_datetime = parse_datetime(expires_at)

            # 创建公告
            announcement = Announcement.objects.create(
                content=cleaned_content,
                html_content=cleaned_content,
                publisher=request.user,
                priority=priority,
                expires_at=expires_at_datetime,
                is_sticky=is_sticky
            )
            
            # 清除缓存
            CacheService.invalidate_announcement_cache()
            
            # 返回成功响应
            return JsonResponse({
                'success': True,
                'message': '公告发布成功！',
                'redirect_url': reverse_lazy('system_management')
            })
            
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': '无效的优先级或过期时间格式！'
            })
        except Exception as e:
            logger.error(f"Error publishing announcement: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '公告发布失败，请稍后重试！'
            })


class UploadImageView(LoginRequiredMixin, View):
    """处理富文本编辑器的图片上传"""

    def post(self, request, *args, **kwargs):
        try:
            if 'file' not in request.FILES:
                return JsonResponse({'error': '没有找到上传的文件'}, status=400)

            uploaded_file = request.FILES['file']
            
            # 使用SecurityService进行文件验证
            security_service = SecurityService()
            
            # 验证文件类型和大小
            if not security_service.validate_image(uploaded_file):
                return JsonResponse({'error': '不支持的文件类型或文件大小超过限制'}, status=400)

            # 生成安全的文件名
            secure_filename = security_service.generate_secure_filename(uploaded_file.name)
            
            # 构建保存路径（确保路径存在）
            save_dir = os.path.join(settings.MEDIA_ROOT, 'uploads', 'images')
            os.makedirs(save_dir, exist_ok=True)
            
            # 完整的文件保存路径
            file_path = os.path.join(save_dir, secure_filename)
            
            # 保存文件
            with open(file_path, 'wb+') as destination:
                for chunk in uploaded_file.chunks():
                    destination.write(chunk)
            
            # 清理旧文件
            security_service.cleanup_old_files(save_dir, max_files=100)
            
            # 返回文件URL（确保URL正确）
            file_url = request.build_absolute_uri(f"{settings.MEDIA_URL}uploads/images/{secure_filename}")
            
            return JsonResponse({
                'location': file_url
            })
            
        except Exception as e:
            # 添加错误日志
            logger.error(f"图片上传失败: {str(e)}")
            return JsonResponse({'error': '图片上传失败，请重试'}, status=500)


class DeleteAnnouncementView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, announcement_id):
        try:
            announcement = get_object_or_404(Announcement, id=announcement_id)
            if not request.user.can_publish_announcements:
                return JsonResponse({
                    'success': False,
                    'message': '您没有权限删除公告！'
                })
            announcement.delete()
            return JsonResponse({
                'success': True,
                'message': '公告删除成功！'
            })
        except Exception as e:
            logger.error(f"删除公告时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '删除公告时出错！'
            })


class BatchDeleteAnnouncementsView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        try:
            if not request.user.can_publish_announcements:
                return JsonResponse({
                    'success': False,
                    'message': '您没有权限删除公告！'
                })
            
            # 从POST请求中获取公告ID列表
            announcement_ids = request.POST.getlist('announcement_ids[]', [])
            if not announcement_ids:
                # 尝试从JSON数据中获取
                try:
                    data = json.loads(request.body)
                    announcement_ids = data.get('announcement_ids', [])
                except json.JSONDecodeError:
                    pass

            if not announcement_ids:
                return JsonResponse({
                    'success': False,
                    'message': '请选择要删除的公告！'
                })
            
            # 删除选中的公告
            deleted_count = Announcement.objects.filter(id__in=announcement_ids).delete()[0]
            return JsonResponse({
                'success': True,
                'message': f'成功删除 {deleted_count} 条公告！'
            })
        except Exception as e:
            logger.error(f"批量删除公告时出错: {str(e)}")
            return JsonResponse({
                'success': False,
                'message': '删除公告时出错！'
            })

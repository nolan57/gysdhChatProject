from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.urls import reverse
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from ..models import User, Announcement, Message, Notice
from ..forms import MessageForm
from ..utils import send_announcement_email
from ..services.cache_service import CacheService
from ..services.security_service import SecurityService  # 导入SecurityService

class ChatView(LoginRequiredMixin, View):
    template_name = 'chat.html'
    
    def get_context_data(self, **kwargs):
        user = kwargs.get('user')
        request_user = kwargs.get('request_user')
        
        # 使用缓存服务获取公告
        announcements = CacheService.get_announcements()
        
        # 获取公共消息
        messages = Message.objects.filter(is_private=False).select_related('sender').order_by('timestamp')[:50]
        
        # 获取私密消息
        if request_user.is_admin or request_user.is_event_staff:
            private_messages = Message.objects.filter(is_private=True).select_related('sender', 'recipient').order_by('timestamp')[:50]
        else:
            private_messages = Message.objects.filter(
                Q(sender=request_user) | Q(recipient=request_user),
                is_private=True
            ).select_related('sender', 'recipient').order_by('timestamp')[:50]

        # 获取当前激活的注意事项
        active_notice = Notice.objects.filter(is_active=True).first()

        context = {
            'user': user,
            'request': {'user': request_user},  # 添加 request.user 到上下文
            'announcements': announcements,
            'messages': messages,
            'private_messages': private_messages,
            'form': MessageForm(),
            'announcement_toggle': False,
            'private_message_toggle': False,
            'active_notice': active_notice,
            'rooms': [{'id': user.id, 'name': '会务沟通', 'description': '所有用户都可以访问的公共聊天室'}],
            'current_room': {'id': user.id, 'name': '会务沟通'}
        }
        return context

    def get(self, request, user_id):
        if not request.user.is_authenticated:
            return redirect('login')
        
        # 更新用户在线状态
        request.user.is_online = True
        request.user.save()

        user = get_object_or_404(User, id=user_id)
        return render(request, self.template_name, self.get_context_data(user=user, request_user=request.user))

    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        
        # 检查是否是回复消息
        reply_to = request.POST.get('reply_to')
        if reply_to:
            try:
                original_message = Message.objects.get(id=reply_to)
                content = request.POST.get('content')
                file = request.FILES.get('file')
                
                if not content and not file:
                    return JsonResponse({'status': 'error', 'message': '请输入消息或选择文件'})
                
                # 处理文件上传
                if file:
                    file_name = file.name
                    file_path = default_storage.save(f'{file_name}', ContentFile(file.read()))
                
                # 创建回复消息
                message = Message.objects.create(
                    sender=user,
                    content=content,
                    is_private=True,
                    recipient=original_message.sender,
                    reply_to=original_message  # 添加对原消息的引用
                )
                
                # 如果有文件，保存文件
                if file:
                    message.file = file
                    message.save()
                
                # 清除相关缓存
                CacheService.invalidate_private_message_cache()  # 清除所有私密消息缓存
                CacheService.invalidate_private_message_cache(user.id)  # 清除发送者的缓存
                CacheService.invalidate_private_message_cache(original_message.sender.id)  # 清除原消息发送者的缓存
                if message.recipient:
                    CacheService.invalidate_private_message_cache(message.recipient.id)  # 清除接收者的缓存
                
                return JsonResponse({'status': 'success'})
            except Message.DoesNotExist:
                return JsonResponse({'status': 'error', 'message': '原消息不存在'})
        
        # 原有的消息处理逻辑
        form = MessageForm(request.POST, request.FILES)
        
        if not form.is_valid():
            return render(request, self.template_name, self.get_context_data(user=user, request_user=request.user))

        announcement_toggle = request.POST.get('announcement_toggle') == 'on'
        private_message_toggle = request.POST.get('private_message_toggle') == 'on'
        
        file = request.FILES.get('file')
        content = request.POST.get('content')

        if not file and not content:
            context = self.get_context_data(user=user, request_user=request.user)
            context['error_message'] = '请输入消息或选择文件。'
            return render(request, self.template_name, context)

        if file:
            file_name = file.name
            file_path = default_storage.save(f'{file_name}', ContentFile(file.read()))

        # 检查是否为公告
        if announcement_toggle and user.can_publish_announcements:
            # 清理和验证HTML内容
            cleaned_content = SecurityService.sanitize_html(content)
            
            # 创建公告
            announcement = Announcement.objects.create(
                content=cleaned_content,
                html_content=cleaned_content,
                publisher=user
            )
            if file:
                announcement.file = file
                announcement.save()
            
            # 清除公告缓存
            CacheService.invalidate_announcement_cache()

            # send_announcement_email(announcement)
            
            return redirect(reverse('chat_view', kwargs={'user_id': user_id}))
            
        # 检查是否为私密消息
        if private_message_toggle and user.can_private_message:
            # 创建私密消息
            message = Message.objects.create(
                sender=user,
                content=content,
                is_private=True,
                recipient=User.objects.filter(
                    Q(is_admin=True) | Q(is_event_staff=True)
                ).first()
            )
            if file:
                message.file = file
                message.save()
            
            # 清除私密消息缓存
            CacheService.invalidate_message_cache()  # 清除所有消息缓存，包括私密消息列表
            CacheService.invalidate_private_message_cache()  # 清除所有私密消息缓存
            CacheService.invalidate_private_message_cache(user.id)  # 清除发送者的缓存
            if message.recipient:
                CacheService.invalidate_private_message_cache(message.recipient.id)  # 清除接收者的缓存
        else:
            # 创建普通消息
            message = Message.objects.create(
                sender=user,
                content=content,
                is_private=False
            )
            if file:
                message.file = file
                message.save()
            
            # 清除公共消息缓存
            CacheService.invalidate_message_cache()
        
        return redirect(reverse('chat_view', kwargs={'user_id': user_id}) + '#latest')

class ReplyView(LoginRequiredMixin, View):
    def get(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        sender = message.sender
        data = {
            'messageId': message_id,
            'senderName': sender.name,
            'content': message.content,
        }
        return JsonResponse(data)

class ReplyReplyView(LoginRequiredMixin, View):
    template_name = 'chat.html'

    def post(self, request, user_id):
        try:
            reply_content = request.POST.get('floating_reply_content', '')
            query_id = int(request.POST.get('message_id', ''))
            user = get_object_or_404(User, id=user_id)
            original_message = get_object_or_404(Message, id=query_id)
            
            file = request.FILES.get('file')
            
            if not reply_content and not file:
                return redirect(reverse('chat_view', kwargs={'user_id': user_id}))

            if file:
                file_name = file.name
                file_path = default_storage.save(f'{file_name}', ContentFile(file.read()))

            reply_message = Message.objects.create(
                sender=user,
                content=reply_content,
                is_private=True,
                recipient=original_message.sender,
                file=file if file else None
            )

            # 清除消息缓存
            CacheService.invalidate_message_cache()
            
            return redirect(reverse('chat_view', kwargs={'user_id': user_id}))

        except (ValueError, ObjectDoesNotExist) as e:
            return redirect(reverse('chat_view', kwargs={'user_id': user_id}))

class RecallMessageView(LoginRequiredMixin, View):
    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        
        # 检查权限：只有消息发送者可以撤回
        if message.sender != request.user:
            return JsonResponse({
                'status': 'error',
                'message': '你没有权限撤回这条消息'
            }, status=403)
        
        # 检查时间限制：只能撤回2分钟内的消息
        time_limit = timezone.now() - timezone.timedelta(minutes=2)
        if message.timestamp < time_limit:
            return JsonResponse({
                'status': 'error',
                'message': '只能撤回2分钟内的消息'
            }, status=400)
        
        try:
            message.is_recalled = True
            message.recalled_at = timezone.now()
            message.save()
            
            # 清除相关缓存
            CacheService.invalidate_message_cache()
            if message.is_private:
                CacheService.invalidate_private_message_cache()
                CacheService.invalidate_private_message_cache(message.sender.id)
                if message.recipient:
                    CacheService.invalidate_private_message_cache(message.recipient.id)
            
            # 发送WebSocket通知
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'chat_public',
                {
                    'type': 'message_status',
                    'message_id': str(message.id),
                    'status': 'recalled'
                }
            )
            
            return JsonResponse({
                'status': 'success',
                'message': '消息已撤回'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'撤回失败：{str(e)}'
            }, status=500)

class DeleteMessageView(LoginRequiredMixin, View):
    def post(self, request, message_id):
        message = get_object_or_404(Message, id=message_id)
        
        # 检查权限：只有管理员和工作人员可以删除其他人的消息
        if not (request.user.is_admin or request.user.is_event_staff):
            return JsonResponse({
                'status': 'error',
                'message': '你没有权限删除这条消息'
            }, status=403)
        
        try:
            # 记录删除操作
            message.is_deleted = True
            message.deleted_at = timezone.now()
            message.deleted_by = request.user
            message.save()
            
            # 清除相关缓存
            CacheService.invalidate_message_cache()
            if message.is_private:
                CacheService.invalidate_private_message_cache()
                CacheService.invalidate_private_message_cache(message.sender.id)
                if message.recipient:
                    CacheService.invalidate_private_message_cache(message.recipient.id)
            
            # 发送WebSocket通知
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                'chat_public',
                {
                    'type': 'message_status',
                    'message_id': str(message.id),
                    'status': 'deleted'
                }
            )
            
            return JsonResponse({
                'status': 'success',
                'message': '消息已删除'
            })
        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'删除失败：{str(e)}'
            }, status=500)

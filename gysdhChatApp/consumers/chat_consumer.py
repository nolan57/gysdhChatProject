import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from ..models import Message, User
from ..services.cache_service import CacheService
from celery import shared_task
from django.core.cache import cache

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        self.user = self.scope['user']

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

        # 发送用户在线状态
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'status': 'online'
            }
        )

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

        # 发送用户离线状态
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'user_status',
                'user_id': str(self.user.id),
                'status': 'offline'
            }
        )

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type', 'chat_message')
        
        if message_type == 'chat_message':
            await self.handle_chat_message(text_data_json)
        elif message_type == 'message_status':
            await self.handle_message_status(text_data_json)

    async def handle_chat_message(self, data):
        message = data['message']
        is_private = data.get('is_private', False)
        recipient_id = data.get('recipient_id')
        reply_to_id = data.get('reply_to_id')

        # 保存消息到数据库
        saved_message = await self.save_message(
            content=message,
            is_private=is_private,
            recipient_id=recipient_id,
            reply_to_id=reply_to_id
        )

        # 构建消息数据
        message_data = {
            'type': 'chat_message',
            'message': {
                'id': str(saved_message.id),
                'content': message,
                'sender_id': str(self.user.id),
                'sender_name': self.user.name,
                'is_private': is_private,
                'recipient_id': recipient_id,
                'reply_to_id': reply_to_id,
                'timestamp': saved_message.timestamp.isoformat(),
            }
        }

        # 发送消息
        if is_private and recipient_id:
            # 私聊消息只发送给接收者和发送者
            for user_id in [str(self.user.id), recipient_id]:
                await self.channel_layer.group_send(
                    f'chat_user_{user_id}',
                    message_data
                )
        else:
            # 群聊消息发送给所有人
            await self.channel_layer.group_send(
                self.room_group_name,
                message_data
            )

    async def handle_message_status(self, data):
        message_id = data.get('message_id')
        status = data.get('status')  # 'recalled' or 'deleted'
        
        if not message_id or not status:
            return
        
        # 发送消息状态更新
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'message_status',
                'message_id': message_id,
                'status': status
            }
        )

    async def chat_message(self, event):
        """处理聊天消息"""
        await self.send(text_data=json.dumps(event))

    async def message_status(self, event):
        """处理消息状态更新"""
        await self.send(text_data=json.dumps(event))

    async def user_status(self, event):
        """处理用户状态更新"""
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_message(self, content, is_private=False, recipient_id=None, reply_to_id=None):
        """保存消息到数据库"""
        # 使用缓存获取recipient和reply_to
        if recipient_id:
            recipient = CacheService.get_user(recipient_id)
            if not recipient:
                recipient = User.objects.get(id=recipient_id)
                CacheService.set_user(recipient_id, recipient)
        else:
            recipient = None
            
        if reply_to_id:
            reply_to = CacheService.get_message(reply_to_id)
            if not reply_to:
                reply_to = Message.objects.get(id=reply_to_id)
                CacheService.set_message(reply_to_id, reply_to)
        else:
            reply_to = None
        
        message = Message.objects.create(
            content=content,
            sender=self.user,
            is_private=is_private,
            recipient=recipient,
            reply_to=reply_to,
            timestamp=timezone.now()
        )
        
        # 使用延迟任务来清除缓存
        cache.set(f'message_{message.id}', message)  # 立即缓存新消息
        
        # 使用Celery任务异步清除缓存
        @shared_task
        def clear_message_cache():
            CacheService.invalidate_message_cache()
            if is_private:
                CacheService.invalidate_private_message_cache()
                CacheService.invalidate_private_message_cache(self.user.id)
                if recipient:
                    CacheService.invalidate_private_message_cache(recipient.id)
        
        clear_message_cache.apply_async(countdown=60)  # 60秒后执行缓存清理
        
        return message

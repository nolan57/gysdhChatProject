import json
from channels.generic.websocket import AsyncWebsocketConsumer
from .services.chat_service import ChatService
from .models import Message, User
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'
        
        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message_type = text_data_json.get('type')
        content = text_data_json.get('content')
        sender_id = text_data_json.get('sender_id')
        is_private = text_data_json.get('is_private', False)
        recipient_id = text_data_json.get('recipient_id')
        reply_to_id = text_data_json.get('reply_to_id')
        file_data = text_data_json.get('file')  # 添加文件数据

        # 使用服务层保存消息
        message = await ChatService.save_message(
            content=content,
            sender_id=sender_id,
            is_private=is_private,
            recipient_id=recipient_id,
            reply_to_id=reply_to_id,
            file_data=file_data  # 传递文件数据
        )

        # 使用服务层格式化消息数据
        message_data = ChatService.format_message_data(message)

        # 发送消息到群组
        await self.channel_layer.group_send(self.room_group_name, message_data)

    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))

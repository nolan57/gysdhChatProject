from channels.db import database_sync_to_async
from django.utils import timezone
from ..models import Message, User
import base64
import os
from django.core.files.base import ContentFile
from typing import Optional, Dict
from .validators import FileValidator, RateLimitValidator
from .filters import ContentFilter
import logging

logger = logging.getLogger(__name__)

class ChatService:
    def __init__(self):
        self.file_validator = FileValidator()
        self.rate_limit_validator = RateLimitValidator()
        self.content_filter = ContentFilter()

    def _handle_file(self, message: Message, file_data: Dict) -> None:
        """处理文件上传"""
        try:
            format, content = file_data['content'].split(';base64,')
            binary_content = base64.b64decode(content)
            message.file.save(
                file_data['name'], 
                ContentFile(binary_content), 
                save=True
            )
        except Exception as e:
            logger.error(f"File upload failed: {str(e)}")
            raise ValueError("文件上传失败，请重试")

    @database_sync_to_async
    def save_message(self, content: str, sender_id: int, 
                    is_private: bool = False, 
                    recipient_id: Optional[int] = None, 
                    reply_to_id: Optional[int] = None, 
                    file_data: Optional[Dict] = None) -> Message:
        """
        保存消息到数据库
        """
        try:
            # 验证发送频率
            self.rate_limit_validator.validate(sender_id)
            
            # 验证文件
            if file_data:
                self.file_validator.validate(file_data)
            
            # 过滤内容
            filtered_content = self.content_filter.filter(content)
            
            # 获取相关对象
            sender = User.objects.get(id=sender_id)
            recipient = (User.objects.get(id=recipient_id) 
                       if recipient_id else None)
            reply_to = (Message.objects.get(id=reply_to_id) 
                       if reply_to_id else None)
            
            # 创建消息
            message = Message.objects.create(
                content=filtered_content,
                sender=sender,
                is_private=is_private,
                recipient=recipient,
                reply_to=reply_to,
                timestamp=timezone.now()
            )

            # 处理文件上传
            if file_data:
                self._handle_file(message, file_data)
            
            return message
            
        except User.DoesNotExist:
            logger.error(f"User not found: {sender_id}")
            raise ValueError("用户不存在")
        except Message.DoesNotExist:
            logger.error(f"Reply message not found: {reply_to_id}")
            raise ValueError("回复的消息不存在")
        except ValueError as e:
            # 重新抛出验证错误
            raise
        except Exception as e:
            # 记录未预期的错误
            logger.error(f"Error saving message: {str(e)}")
            raise ValueError("消息发送失败，请重试")

    @staticmethod
    def format_message_data(message: Message) -> Dict:
        """
        格式化消息数据用于WebSocket传输
        """
        try:
            return {
                'type': 'chat_message',
                'message': {
                    'id': message.id,
                    'content': message.content,
                    'sender_id': message.sender.id,
                    'sender_name': message.sender.name,
                    'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    'is_private': message.is_private,
                    'recipient_id': message.recipient.id if message.recipient else None,
                    'reply_to_id': message.reply_to.id if message.reply_to else None,
                    'file': message.file.url if message.file else None,
                    'file_name': os.path.basename(message.file.name) if message.file else None
                }
            }
        except Exception as e:
            logger.error(f"Error formatting message: {str(e)}")
            raise ValueError("消息格式化失败")

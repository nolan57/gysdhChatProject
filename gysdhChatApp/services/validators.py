from abc import ABC, abstractmethod
import os
import base64
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta

class BaseValidator(ABC):
    @abstractmethod
    def validate(self, data: Any) -> bool:
        """验证数据"""
        pass

class FileValidator(BaseValidator):
    def __init__(self, max_size_mb: int = 10, 
                 allowed_extensions: set = None):
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节
        self.allowed_extensions = allowed_extensions or {
            '.jpg', '.jpeg', '.png', '.gif', '.pdf', 
            '.doc', '.docx', '.xls', '.xlsx'
        }

    def validate(self, file_data: Optional[Dict]) -> bool:
        """验证文件大小和类型"""
        if not file_data:
            return True

        # 验证文件大小
        content = file_data.get('content', '').split(';base64,')[1]
        file_size = len(base64.b64decode(content))
        if file_size > self.max_size:
            raise ValueError(f"文件大小不能超过{self.max_size // 1024 // 1024}MB")

        # 验证文件类型
        file_name = file_data.get('name', '')
        ext = os.path.splitext(file_name)[1].lower()
        if ext not in self.allowed_extensions:
            raise ValueError(f"不支持的文件类型: {ext}")

        return True

class RateLimitValidator(BaseValidator):
    def __init__(self, limit: int = 30, window: int = 60):
        self.limit = limit  # 时间窗口内的最大请求数
        self.window = window  # 时间窗口（秒）

    def validate(self, user_id: int) -> bool:
        """验证用户请求频率"""
        cache_key = f'message_rate_{user_id}'
        now = timezone.now()

        # 获取用户最近的消息时间列表
        message_times = cache.get(cache_key, [])
        
        # 清理过期的记录
        message_times = [t for t in message_times 
                        if now - t < timedelta(seconds=self.window)]

        # 检查频率限制
        if len(message_times) >= self.limit:
            raise ValueError(
                f"发送消息过于频繁，请等待 "
                f"{self.window - (now - min(message_times)).seconds} 秒"
            )

        # 添加新的消息时间
        message_times.append(now)
        cache.set(cache_key, message_times, self.window)

        return True

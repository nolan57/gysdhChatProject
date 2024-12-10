from django.core.cache import cache
from django.conf import settings
from ..models import Message, User, Announcement
from typing import List, Optional, Union
import json
from .encryption_service import encryption_service
from django.core.serializers import serialize, deserialize

class CacheService:
    @staticmethod
    def get_cache_key(prefix: str, identifier: Union[int, str]) -> str:
        """生成缓存键"""
        return f"{prefix}:{identifier}"

    @staticmethod
    def _serialize_objects(objects):
        """序列化对象列表"""
        if not objects:
            return None
        serialized_data = serialize('json', objects, use_natural_foreign_keys=True)
        return encryption_service.encrypt(serialized_data)

    @staticmethod
    def _deserialize_objects(encrypted_data):
        """反序列化对象列表"""
        if not encrypted_data:
            return None
        decrypted_data = encryption_service.decrypt(encrypted_data)
        if not decrypted_data:
            return None
        return [obj.object for obj in deserialize('json', decrypted_data)]

    @staticmethod
    def _serialize_object(obj):
        """序列化单个对象"""
        if not obj:
            return None
        serialized_data = serialize('json', [obj], use_natural_foreign_keys=True)
        return encryption_service.encrypt(serialized_data)

    @staticmethod
    def _deserialize_object(encrypted_data):
        """反序列化单个对象"""
        if not encrypted_data:
            return None
        objects = CacheService._deserialize_objects(encrypted_data)
        return objects[0] if objects else None

    @classmethod
    def get_messages(cls, limit: int = 50, offset: int = 0, include_private: bool = False) -> List[Message]:
        """获取消息列表，优先从缓存获取"""
        cache_key = cls.get_cache_key("messages", f"{limit}:{offset}:{include_private}")
        encrypted_data = cache.get(cache_key)
        messages = cls._deserialize_objects(encrypted_data)
        
        if messages is None:
            query = Message.objects.select_related('sender').filter(is_deleted=False)
            if not include_private:
                query = query.filter(is_private=False)
            messages = list(query.order_by('-id')[offset:offset + limit])
            encrypted_data = cls._serialize_objects(messages)
            if encrypted_data:
                cache.set(cache_key, encrypted_data, settings.CACHE_TTL['message'])
        
        return messages or []

    @classmethod
    def get_private_messages(cls, user, limit: int = 50, offset: int = 0) -> List[Message]:
        """获取私密消息列表"""
        from django.db.models import Q
        cache_key = cls.get_cache_key(f"private_messages:{user.id}", f"{limit}:{offset}")
        encrypted_data = cache.get(cache_key)
        messages = cls._deserialize_objects(encrypted_data)
        
        if messages is None:
            if user.is_admin or user.is_event_staff:
                query = Message.objects.filter(is_private=True, is_deleted=False)
            else:
                query = Message.objects.filter(is_private=True, is_deleted=False).filter(
                    Q(recipient=user) |
                    Q(sender=user) |
                    Q(reply_to__sender=user) |
                    Q(reply_to__recipient=user)
                ).distinct()
            
            messages = list(query.select_related('sender').order_by('-id')[offset:offset + limit])
            encrypted_data = cls._serialize_objects(messages)
            if encrypted_data:
                cache.set(cache_key, encrypted_data, settings.CACHE_TTL['message'])
        
        return messages or []

    @classmethod
    def get_user(cls, user_id: int) -> Optional[User]:
        """获取用户信息，优先从缓存获取"""
        cache_key = cls.get_cache_key("user", user_id)
        encrypted_data = cache.get(cache_key)
        user = cls._deserialize_object(encrypted_data)
        
        if user is None:
            try:
                user = User.objects.get(id=user_id)
                encrypted_data = cls._serialize_object(user)
                if encrypted_data:
                    cache.set(cache_key, encrypted_data, settings.CACHE_TTL['user'])
            except User.DoesNotExist:
                return None
        
        return user

    @classmethod
    def get_announcements(cls) -> List[Announcement]:
        """获取公告列表，优先从缓存获取"""
        cache_key = "announcements"
        encrypted_data = cache.get(cache_key)
        announcements = cls._deserialize_objects(encrypted_data)
        
        if announcements is None:
            # 使用 get_active_announcements 方法获取未过期的公告
            announcements = list(Announcement.get_active_announcements()[:50])
            encrypted_data = cls._serialize_objects(announcements)
            if encrypted_data:
                cache.set(cache_key, encrypted_data, settings.CACHE_TTL['announcement'])
        
        return announcements or []

    @classmethod
    def cache_message(cls, message: Message):
        """缓存单条消息"""
        cache_key = cls.get_cache_key("message", message.id)
        encrypted_data = cls._serialize_object(message)
        if encrypted_data:
            cache.set(cache_key, encrypted_data, settings.CACHE_TTL['message'])
        cls.invalidate_message_cache()

    @classmethod
    def get_message(cls, message_id: int) -> Optional[Message]:
        """获取单条消息，优先从缓存获取"""
        cache_key = cls.get_cache_key("message", message_id)
        encrypted_data = cache.get(cache_key)
        message = cls._deserialize_object(encrypted_data)
        
        if message is None:
            try:
                message = Message.objects.select_related('sender').get(id=message_id)
                encrypted_data = cls._serialize_object(message)
                if encrypted_data:
                    cache.set(cache_key, encrypted_data, settings.CACHE_TTL['message'])
            except Message.DoesNotExist:
                return None
        
        return message

    @classmethod
    def invalidate_message_cache(cls):
        """使消息缓存失效"""
        cache.delete_pattern("messages:*")
        cache.delete_pattern("private_messages:*")  # 同时清除私密消息缓存

    @classmethod
    def invalidate_private_message_cache(cls, user_id: Optional[int] = None):
        """使私密消息缓存失效
        
        Args:
            user_id: 如果指定，只清除该用户的私密消息缓存；否则清除所有私密消息缓存
        """
        if user_id is not None:
            cache.delete_pattern(f"private_messages:{user_id}:*")
        else:
            cache.delete_pattern("private_messages:*")

    @classmethod
    def invalidate_user_cache(cls, user_id: int):
        """使用户缓存失效"""
        cache_key = cls.get_cache_key("user", user_id)
        cache.delete(cache_key)

    @classmethod
    def invalidate_announcement_cache(cls):
        """使公告缓存失效"""
        cache_key = "announcements"
        cache.delete(cache_key)

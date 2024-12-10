from django.db.models.signals import post_save
from django.dispatch import receiver
from django.apps import apps
from .services import forward_private_message, forward_announcement
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender='gysdhChatApp.Message')
def handle_message_notification(sender, instance, created, **kwargs):
    """处理消息通知"""
    if not created:  # 只处理新消息
        return
        
    try:
        if instance.is_private:  # 私信
            # 转发私信
            forward_private_message(
                message_id=instance.id,
                sender_name=instance.sender.name,
                sender_email=instance.sender.email,
                recipient_id=instance.recipient.id,
                recipient_email=instance.recipient.email,
                content=instance.content,
                timestamp=instance.timestamp,
                user_is_online=instance.recipient.is_online
            )
        else:  # 公告
            # 获取所有离线用户
            User = apps.get_model('gysdhChatApp', 'User')
            offline_users = list(User.objects.filter(
                is_online=False
            ).values('id', 'email'))
            
            # 转发公告
            forward_announcement(
                message_id=instance.id,
                content=instance.content,
                timestamp=instance.timestamp,
                offline_users=offline_users
            )

    except Exception as e:
        logger.error(f"Failed to process message {instance.id}: {str(e)}")
        raise

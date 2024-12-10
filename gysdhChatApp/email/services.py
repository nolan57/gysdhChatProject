import logging
from django.core.mail import send_mail
from django.utils import timezone
from django.conf import settings
from .models import EmailConfig, EmailForwardRule, EmailForwardLog

logger = logging.getLogger(__name__)

def get_active_email_config():
    """获取当前激活的邮件配置"""
    from ..models import SystemSettings
    settings = SystemSettings.get_settings()
    if not settings:
        return None
    
    # 检查必要的邮件配置是否存在
    if not all([
        settings.email_host,
        settings.email_port,
        settings.email_host_user,
        settings.email_host_password
    ]):
        return None
    
    # 创建一个 EmailConfig 实例来保持兼容性
    config = EmailConfig(
        smtp_host=settings.email_host,
        smtp_port=settings.email_port,
        smtp_user=settings.email_host_user,
        smtp_password=settings.email_host_password,
        use_tls=settings.email_use_tls,
        is_active=True
    )
    
    return config

def should_forward_message(rule, user_is_online):
    """检查是否应该转发消息"""
    if not rule or not rule.is_active:
        return False

    # 检查是否仅在离线时转发
    if rule.forward_when_offline_only and user_is_online:
        return False

    # 检查最小间隔
    if rule.min_interval:
        last_forward = EmailForwardLog.objects.filter(
            rule=rule,
            status='sent'
        ).order_by('-forwarded_at').first()

        if last_forward:
            time_diff = (timezone.now() - last_forward.forwarded_at).total_seconds()
            if time_diff < rule.min_interval:
                return False

    return True

def forward_private_message(message_id, sender_name, sender_email, recipient_id, 
                          recipient_email, content, timestamp, user_is_online):
    """转发私信"""
    try:
        # 获取转发规则
        rule = EmailForwardRule.objects.filter(user_id=recipient_id).first()
        
        if not should_forward_message(rule, user_is_online):
            return

        # 创建转发日志
        forward_log = EmailForwardLog.objects.create(
            rule=rule,
            message_id=message_id,
            message_type='private',  # 使用 message_type 字段记录日志
            recipient_email=recipient_email,
            status='pending'
        )

        # 准备邮件内容
        subject = f'[GYSDH CHAT] 新私信提醒'
        content = f'''您收到来自 {sender_name} 的新私信
发送者邮箱：{sender_email}
发送时间：{timestamp.strftime("%Y-%m-%d %H:%M:%S")}

私信内容：
{content}

---
此邮件由系统自动发送，请勿直接回复。'''

        # 获取邮件配置
        email_config = get_active_email_config()
        if not email_config:
            raise ValueError("未找到有效的邮件配置")

        # 发送邮件
        send_mail(
            subject=subject,
            message=content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )

        # 更新转发日志
        forward_log.status = 'sent'
        forward_log.save()

        logger.info(f"Successfully forwarded message {message_id} to {recipient_email}")

    except Exception as e:
        logger.error(f"Failed to forward message {message_id}: {str(e)}")
        if 'forward_log' in locals():
            forward_log.status = 'failed'
            forward_log.error_message = str(e)
            forward_log.save()
        raise

def forward_announcement(message_id, content, timestamp, offline_users):
    """转发公告"""
    try:
        # 获取邮件配置
        email_config = get_active_email_config()
        if not email_config:
            logger.error("未找到有效的邮件配置，无法发送公告邮件")
            return

        # 准备邮件内容
        subject = f'[GYSDH CHAT] 新公告提醒'
        email_content = f'''系统发布了新公告
发布时间：{timestamp.strftime("%Y-%m-%d %H:%M:%S")}

公告内容：
{content}

---
此邮件由系统自动发送，请勿直接回复。'''

        # 为每个离线用户创建转发日志并发送邮件
        for user in offline_users:
            try:
                # 获取用户的转发规则
                rule = EmailForwardRule.objects.filter(user_id=user['id']).first()
                
                if not should_forward_message(rule, False):  # False 表示用户离线
                    continue

                # 创建转发日志
                forward_log = EmailForwardLog.objects.create(
                    rule=rule,
                    message_id=message_id,
                    message_type='announcement',  # 使用 message_type 字段记录日志
                    recipient_email=user['email'],
                    status='pending'
                )

                # 发送邮件
                send_mail(
                    subject=subject,
                    message=email_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user['email']],
                    fail_silently=False,
                )

                # 更新转发日志
                forward_log.status = 'sent'
                forward_log.save()

                logger.info(f"Successfully forwarded announcement {message_id} to {user['email']}")

            except Exception as e:
                logger.error(f"Failed to forward announcement {message_id} to {user['email']}: {str(e)}")
                if 'forward_log' in locals():
                    forward_log.status = 'failed'
                    forward_log.error_message = str(e)
                    forward_log.save()

    except Exception as e:
        logger.error(f"Failed to forward announcement {message_id}: {str(e)}")
        raise

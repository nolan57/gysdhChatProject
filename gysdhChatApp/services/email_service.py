from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string

def send_user_credentials_email(user, password=None, is_new=True, is_reset=False):
    """
    发送用户凭据邮件
    :param user: User对象
    :param password: 用户密码（如果需要发送）
    :param is_new: 是否是新用户
    :param is_reset: 是否是密码重置
    """
    if not user.email:
        return False

    if is_new:
        subject = '欢迎使用GYSDH聊天系统 - 账号信息'
        template = 'email/new_user_credentials.html'
    elif is_reset:
        subject = 'GYSDH聊天系统 - 密码重置通知'
        template = 'email/password_reset.html'
    else:
        subject = 'GYSDH聊天系统 - 账号信息更新'
        template = 'email/user_update.html'

    context = {
        'user': user,
        'password': password,
        'is_new': is_new,
        'is_reset': is_reset
    }

    try:
        message = render_to_string(template, context)
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=message,
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"发送邮件失败: {str(e)}")
        return False

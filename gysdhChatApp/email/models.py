from django.db import models
from django.utils import timezone

class EmailConfig(models.Model):
    """邮件配置模型"""
    smtp_host = models.CharField('SMTP服务器', max_length=255)
    smtp_port = models.IntegerField('SMTP端口')
    smtp_user = models.CharField('SMTP用户名', max_length=255)
    smtp_password = models.CharField('SMTP密码', max_length=255)
    use_tls = models.BooleanField('使用TLS', default=True)
    is_active = models.BooleanField('是否启用', default=True)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '邮件配置'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"{self.smtp_host}:{self.smtp_port}"

class EmailForwardRule(models.Model):
    """邮件转发规则"""
    user_id = models.IntegerField('用户ID')
    user_email = models.EmailField('用户邮箱', max_length=255)
    is_active = models.BooleanField('是否启用', default=True)
    forward_when_offline_only = models.BooleanField('仅离线时转发', default=True)
    min_interval = models.IntegerField(
        '最小转发间隔(秒)',
        default=300,
        help_text='两次转发之间的最小间隔时间'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)

    class Meta:
        verbose_name = '转发规则'
        verbose_name_plural = verbose_name

    def __str__(self):
        return f"用户{self.user_id}的转发规则"

class EmailForwardLog(models.Model):
    """邮件转发日志"""
    STATUS_CHOICES = [
        ('pending', '待发送'),
        ('sent', '已发送'),
        ('failed', '发送失败'),
    ]

    rule = models.ForeignKey(
        EmailForwardRule,
        on_delete=models.CASCADE,
        related_name='forward_logs',
        verbose_name='转发规则'
    )
    message_id = models.IntegerField('消息ID')
    message_type = models.CharField('消息类型', max_length=20, choices=[
        ('private', '私信'),
        ('announcement', '公告'),
    ])
    recipient_email = models.EmailField('接收者邮箱', max_length=255)
    status = models.CharField(
        '状态',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField('错误信息', blank=True)
    forwarded_at = models.DateTimeField('转发时间', default=timezone.now)

    class Meta:
        verbose_name = '转发日志'
        verbose_name_plural = verbose_name
        ordering = ['-forwarded_at']

    def __str__(self):
        return f"{self.rule} - {self.forwarded_at}"

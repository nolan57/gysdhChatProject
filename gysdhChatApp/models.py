from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.shortcuts import get_object_or_404
from django.utils import timezone
import random
import string
from django.conf import settings
from cryptography.fernet import Fernet
import base64

def _get_fernet():
    """获取Fernet实例用于加密解密"""
    if not hasattr(settings, 'ENCRYPTION_KEY'):
        raise ImproperlyConfigured('ENCRYPTION_KEY must be set in settings')
    
    # 确保密钥是32位的URL安全的base64编码
    key = settings.ENCRYPTION_KEY
    if not isinstance(key, bytes):
        key = key.encode()
    
    # 如果密钥不是32位，进行填充或截断
    key = base64.urlsafe_b64encode(key.ljust(32)[:32])
    return Fernet(key)

def encrypt_text(text):
    """加密文本"""
    if not text:
        return ''
    if isinstance(text, str):
        text = text.encode()
    return _get_fernet().encrypt(text).decode()

def decrypt_text(encrypted_text):
    """解密文本"""
    if not encrypted_text:
        return ''
    if isinstance(encrypted_text, str):
        encrypted_text = encrypted_text.encode()
    try:
        return _get_fernet().decrypt(encrypted_text).decode()
    except Exception:
        return ''

def generate_unique_number():
    """
    生成唯一的6位数用户代码
    """
    return str(random.randint(100000, 999999))

def generate_password():
    """
    生成8位随机密码，包含数字和字母
    """
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(8))

class UserManager(BaseUserManager):
    def create_user(self, name, companyCode, email, password=None, number=None):
        if not email:
            raise ValueError('The Email field must be set')
        
        # 如果没有提供密码，则自动生成
        if not password:
            password = generate_password()
            
        user = self.model(
            name=name,
            companyCode=companyCode,
            email=self.normalize_email(email),
            number=number if number else generate_unique_number(),
            original_password=password  # 保存原始密码
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, name, companyCode, email, password=None, number=None):
        user = self.create_user(
            name=name,
            companyCode=companyCode,
            email=email,
            password=password,
            number=number
        )
        user.is_admin = True
        user.save(using=self._db)
        return user

class UserGroup(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='组名')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        ordering = ['name']
        verbose_name = '用户组'
        verbose_name_plural = '用户组'

    def __str__(self):
        return self.name

class User(AbstractBaseUser):
    number = models.CharField(max_length=6, unique=True, default=generate_unique_number, editable=False)
    name = models.CharField(max_length=100)
    companyCode = models.CharField(max_length=6)
    email = models.EmailField(max_length=255, unique=True, default='default@example.com')
    phone = models.CharField(max_length=20, blank=True, verbose_name='电话号码')
    _encrypted_original_password = models.TextField(editable=True, default='')
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用户组', related_name='users')
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    can_publish_announcements = models.BooleanField(default=False)
    can_private_message = models.BooleanField(default=False)
    is_event_staff = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = 'number'
    REQUIRED_FIELDS = ['name', 'companyCode', 'email']

    def __str__(self):
        return f"{self.name} ({self.number})"

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin

    @property
    def original_password(self):
        """获取解密后的原始密码"""
        if not self._encrypted_original_password:
            return ''
        return decrypt_text(self._encrypted_original_password)

    @original_password.setter
    def original_password(self, value):
        """加密存储原始密码"""
        if not value:
            self._encrypted_original_password = ''
        else:
            self._encrypted_original_password = encrypt_text(value)

    def check_original_password(self, raw_password):
        """验证原始密码"""
        return decrypt_text(self._encrypted_original_password) == raw_password

    def save(self, *args, **kwargs):
        if self._state.adding:
            while User.objects.filter(number=self.number).exists():
                self.number = generate_unique_number()
        super().save(*args, **kwargs)

class Announcement(models.Model):
    PRIORITY_CHOICES = [
        (1, '低'),
        (2, '中'),
        (3, '高'),
        (4, '紧急'),
    ]

    content = models.TextField(help_text='支持富文本格式')
    html_content = models.TextField(blank=True, help_text='渲染后的HTML内容')
    publisher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_announcements'
    )
    file = models.FileField(upload_to='Announcement', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=1,
        verbose_name='优先级'
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='过期时间',
        help_text='为空表示永不过期'
    )
    is_sticky = models.BooleanField(
        default=False,
        verbose_name='置顶',
        help_text='置顶的公告会始终显示在列表顶部'
    )

    class Meta:
        ordering = ['-is_sticky', '-priority', '-timestamp']
        verbose_name = '公告'
        verbose_name_plural = '公告'

    def __str__(self):
        return f"{self.get_priority_display()}级公告 - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @property
    def is_expired(self):
        """检查公告是否已过期"""
        if self.expires_at is None:
            return False
        return timezone.now() > self.expires_at

    @classmethod
    def get_active_announcements(cls):
        """获取所有未过期的公告"""
        now = timezone.now()
        return cls.objects.filter(
            models.Q(expires_at__isnull=True) |
            models.Q(expires_at__gt=now)
        ).order_by('-is_sticky', '-priority', '-timestamp')

    def save(self, *args, **kwargs):
        # 直接使用content作为html_content，因为内容已经是HTML格式
        self.html_content = self.content
        super().save(*args, **kwargs)

class Message(models.Model):
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='sent_messages'
    )
    content = models.TextField(null=True, blank=True)
    file = models.FileField(upload_to='Message', null=True, blank=True)
    timestamp = models.DateTimeField(default=timezone.now)
    is_private = models.BooleanField(default=False)
    recipient = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='received_messages'
    )
    reply_to = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    is_recalled = models.BooleanField(default=False, verbose_name='是否已撤回')
    recalled_at = models.DateTimeField(null=True, blank=True, verbose_name='撤回时间')
    is_deleted = models.BooleanField(default=False, verbose_name='是否已删除')
    deleted_at = models.DateTimeField(null=True, blank=True, verbose_name='删除时间')
    deleted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='deleted_messages',
        verbose_name='删除者'
    )

    def __str__(self):
        return f"Message from {self.sender.name if self.sender else 'Unknown'} at {self.timestamp}"

    class Meta:
        ordering = ['timestamp']

class Notice(models.Model):
    content = models.TextField(verbose_name='注意事项内容')
    publisher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='published_notices',
        verbose_name='发布者'
    )
    is_active = models.BooleanField(default=True, verbose_name='是否激活')
    timestamp = models.DateTimeField(default=timezone.now, verbose_name='发布时间')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = '注意事项'
        verbose_name_plural = '注意事项'

    def __str__(self):
        return f"注意事项 - {self.timestamp}"

class FileDownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    file_name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50, choices=[
        ('message', '消息文件'),
        ('announcement', '公告文件'),
    ])
    content_type = models.CharField(max_length=100)
    file_size = models.BigIntegerField()
    source_id = models.IntegerField()  # 消息或公告的ID
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)

    class Meta:
        ordering = ['-downloaded_at']
        verbose_name = '文件下载记录'
        verbose_name_plural = '文件下载记录'

    def __str__(self):
        return f"{self.user.name} - {self.file_name} ({self.downloaded_at})"

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name='标签名')
    color = models.CharField(max_length=20, default='#3B82F6', verbose_name='标签颜色')
    description = models.TextField(blank=True, verbose_name='描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tags',
        verbose_name='创建者'
    )

    class Meta:
        ordering = ['name']
        verbose_name = '标签'
        verbose_name_plural = '标签'

    def __str__(self):
        return self.name

class UserTag(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_tags', verbose_name='用户')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='tagged_users', verbose_name='标签')
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='添加时间')
    added_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='added_user_tags',
        verbose_name='添加者'
    )

    class Meta:
        unique_together = ('user', 'tag')
        ordering = ['added_at']
        verbose_name = '用户标签'
        verbose_name_plural = '用户标签'

    def __str__(self):
        return f"{self.user.name} - {self.tag.name}"

class SystemSettings(models.Model):
    chat_title = models.CharField(max_length=100, default='GYSDH CHAT', verbose_name='聊天室标题')
    chat_area_title = models.CharField(max_length=100, default='聊天区域', verbose_name='聊天区域标题')
    email_host = models.CharField(max_length=100, default='smtp.qq.com', verbose_name='邮件服务器')
    email_port = models.IntegerField(default=587, verbose_name='服务器端口')
    email_host_user = models.EmailField(max_length=255, default='', verbose_name='邮箱账号')
    email_host_password = models.CharField(max_length=100, default='', verbose_name='授权码')
    email_use_tls = models.BooleanField(default=True, verbose_name='使用TLS')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='system_settings_updates',
        verbose_name='更新者'
    )

    class Meta:
        verbose_name = '系统设置'
        verbose_name_plural = '系统设置'

    def __str__(self):
        return f'系统设置 (更新于 {self.updated_at})'

    @classmethod
    def get_settings(cls):
        settings = cls.objects.first()
        if not settings:
            settings = cls.objects.create()
        return settings

class EmailTemplate(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name='模板名称')
    subject = models.CharField(max_length=200, verbose_name='邮件主题')
    content = models.TextField(verbose_name='邮件内容')
    description = models.TextField(blank=True, verbose_name='模板描述')
    variables = models.JSONField(default=dict, verbose_name='可用变量',
                               help_text='以JSON格式存储可用于此模板的变量名及其描述')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_email_templates',
        verbose_name='创建者'
    )

    class Meta:
        ordering = ['name']
        verbose_name = '邮件模板'
        verbose_name_plural = '邮件模板'

    def __str__(self):
        return self.name

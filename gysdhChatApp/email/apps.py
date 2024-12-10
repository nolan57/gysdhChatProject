from django.apps import AppConfig

class EmailConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gysdhChatApp.email'
    verbose_name = '邮件服务'

    def ready(self):
        """加载信号处理器"""
        from . import signals  # 在应用准备好后导入信号

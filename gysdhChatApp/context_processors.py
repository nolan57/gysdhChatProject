from .models import SystemSettings

def system_settings(request):
    """
    添加系统设置到模板上下文
    """
    return {
        'settings': SystemSettings.get_settings()
    }

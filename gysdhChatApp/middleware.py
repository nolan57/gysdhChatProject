from django.utils import timezone
from datetime import timedelta
from django.contrib.auth import get_user_model

User = get_user_model()

class UserActivityMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # 更新用户最后活动时间
            request.user.last_activity = timezone.now()
            request.user.is_online = True
            request.user.save()

            # 将超过5分钟没有活动的用户标记为离线
            User.objects.filter(
                last_activity__lt=timezone.now() - timedelta(minutes=5)
            ).update(is_online=False)

        response = self.get_response(request)
        return response

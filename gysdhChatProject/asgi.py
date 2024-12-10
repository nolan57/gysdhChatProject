"""
ASGI config for gysdhChatProject project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os
import logging
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)  

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gysdhChatProject.settings')
django.setup()  

from gysdhChatApp.routing import websocket_urlpatterns  

# 性能监控中间件
class PerformanceMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        import time
        start_time = time.time()
        
        # 只在 WebSocket 连接中添加性能监控
        if scope["type"] == "websocket":
            from channels.layers import get_channel_layer
            channel_layer = get_channel_layer()
            # 等待连接建立后再添加到组
            if scope.get('channel_name'):
                await channel_layer.group_add("stats", scope['channel_name'])
        
        try:
            return await self.inner(scope, receive, send)
        finally:
            duration = time.time() - start_time
            if duration > 1.0:  
                logger.warning(f"Slow WebSocket operation: {duration:.2f}s for {scope.get('path', 'unknown')}")
            if scope["type"] == "websocket" and scope.get('channel_name'):
                await channel_layer.group_discard("stats", scope['channel_name'])

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AllowedHostsOriginValidator(  
        PerformanceMiddleware(  
            SessionMiddlewareStack(  
                AuthMiddlewareStack(
                    URLRouter(websocket_urlpatterns)
                )
            )
        )
    ),
})

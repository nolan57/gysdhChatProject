"""
gysdhChatProject URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from gysdhChatApp.views import tag_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gysdhChatApp.urls')),
    path('conference/', include('conferenceApp.urls')),  
    # 标签管理
    path('tags/', tag_views.tag_list, name='tag_list'),
    path('tags/create/', tag_views.create_tag, name='create_tag'),
    path('tags/<int:tag_id>/update/', tag_views.update_tag, name='update_tag'),
    path('tags/<int:tag_id>/delete/', tag_views.delete_tag, name='delete_tag'),
    path('users/<int:user_id>/tags/', tag_views.manage_user_tags, name='manage_user_tags'),
    path('api/tags/add/', tag_views.ajax_add_user_tag, name='ajax_add_user_tag'),
    path('api/tags/remove/', tag_views.ajax_remove_user_tag, name='ajax_remove_user_tag'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

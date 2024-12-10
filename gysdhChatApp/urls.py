from django.urls import path
from .views import (
    LoginView, LogoutView, ReplyView, ReplyReplyView,
    download_message_file, download_announcement_file, UploadImageView,
    SystemManagementView, UpdateSystemSettingsView, UpdateEmailSettingsView, SendTestEmailView,
    download_file, download_logs
)
from .views.chat_views import ChatView, RecallMessageView, DeleteMessageView
from .views.system_views import PublishNoticeView, FileDownloadLogView
from .views.notice_views import (
    QuickPublishNoticeView, QuickPublishAnnouncementView,
    DeleteAnnouncementView, BatchDeleteAnnouncementsView
)
from .views.user_views import (
    CreateUserView, UserListView, DeleteUserView, UpdateUserView, ResetPasswordView,
    UserGroupListView, CreateUserGroupView, UpdateUserGroupView, DeleteUserGroupView, UserGroupDetailView, BatchAssignGroupView,
    BatchDeleteUsersView, DeleteUsersByGroupView, UserDetailView, BatchAssignTagsView
)
from .views.admin_views import ImportUsersView
from .views.export_views import (
    ExportUsersView, ExportMessagesView, ExportAnnouncementsView,
    ExportManagementView
)
from .views.email_template_views import (
    EmailTemplateListView, EmailTemplateCreateView,
    EmailTemplateUpdateView, EmailTemplateDeleteView,
    EmailTemplatePreviewView, BatchEmailSendView
)
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    # 登录相关
    path('', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # 聊天相关
    path('chat/<int:user_id>/', ChatView.as_view(), name='chat_view'),
    path('reply/<int:message_id>/', ReplyView.as_view(), name='reply_view'),
    path('reply_reply/<int:user_id>/', ReplyReplyView.as_view(), name='reply_reply_view'),
    path('message/recall/<int:message_id>/', RecallMessageView.as_view(), name='recall_message'),
    path('message/delete/<int:message_id>/', DeleteMessageView.as_view(), name='delete_message'),
    
    # 文件下载相关
    path('download/<str:file_type>/<int:file_id>/', download_file, name='download_file'),  
    path('download/message/<int:file_id>/', download_message_file, name='download_message_file'),  
    path('download/announcement/<int:file_id>/', download_announcement_file, name='download_announcement_file'),  
    path('system/download-logs/', download_logs, name='download_logs'),
    
    # 系统管理
    path('system-management/', SystemManagementView.as_view(), name='system_management'),
    path('system/settings/update/', UpdateSystemSettingsView.as_view(), name='update_system_settings'),
    path('system/settings/email/update/', UpdateEmailSettingsView.as_view(), name='update_email_settings'),
    path('system/settings/email/test/', SendTestEmailView.as_view(), name='send_test_email'),
    path('publish-notice/', PublishNoticeView.as_view(), name='publish_notice'),
    path('quick-publish-notice/', QuickPublishNoticeView.as_view(), name='quick_publish_notice'),
    path('quick-publish-announcement/', QuickPublishAnnouncementView.as_view(), name='quick_publish_announcement'),
    path('upload-image/', UploadImageView.as_view(), name='upload_image'),
    path('file-download-log/', FileDownloadLogView.as_view(), name='file_download_log'),
    path('email-templates/', EmailTemplateListView.as_view(), name='template_list'),
    path('email-templates/create/', EmailTemplateCreateView.as_view(), name='template_create'),
    path('email-templates/<int:pk>/update/', EmailTemplateUpdateView.as_view(), name='template_update'),
    path('email-templates/<int:pk>/delete/', EmailTemplateDeleteView.as_view(), name='template_delete'),
    path('email-templates/<int:pk>/preview/', EmailTemplatePreviewView.as_view(), name='template_preview'),
    path('users/batch-send-email/', BatchEmailSendView.as_view(), name='batch_send_email'),
    # 用户管理
    path('user/list/', UserListView.as_view(), name='user_list'),
    path('user/create/', CreateUserView.as_view(), name='create_user'),
    path('user/update/<int:user_id>/', UpdateUserView.as_view(), name='update_user'),
    path('user/delete/<int:user_id>/', DeleteUserView.as_view(), name='delete_user'),
    path('user/<int:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('user/batch-delete/', BatchDeleteUsersView.as_view(), name='batch_delete_users'),
    path('user/delete-by-group/<int:group_id>/', DeleteUsersByGroupView.as_view(), name='delete_users_by_group'),
    path('user/import/', ImportUsersView.as_view(), name='import_users'),
    path('users/<int:user_id>/reset-password/', ResetPasswordView.as_view(), name='reset_password'),
    path('users/batch-assign-group/', BatchAssignGroupView.as_view(), name='batch_assign_group'),
    path('users/batch-assign-tags/', BatchAssignTagsView.as_view(), name='batch_assign_tags'),
    
    # 用户组管理
    path('group/list/', UserGroupListView.as_view(), name='group_list'),
    path('group/create/', CreateUserGroupView.as_view(), name='create_group'),
    path('group/update/<int:group_id>/', UpdateUserGroupView.as_view(), name='update_group'),
    path('group/delete/<int:group_id>/', DeleteUserGroupView.as_view(), name='delete_group'),
    path('group/<int:group_id>/', UserGroupDetailView.as_view(), name='group_detail'),
    path('group/batch-assign/', BatchAssignGroupView.as_view(), name='batch_assign_group'),
    
    # 数据导出
    path('export/', ExportManagementView.as_view(), name='export_management'),
    path('export/users/', ExportUsersView.as_view(), name='export_users'),
    path('export/messages/', ExportMessagesView.as_view(), name='export_messages'),
    path('export/announcements/', ExportAnnouncementsView.as_view(), name='export_announcements'),
    
    # 公告管理
    path('delete_announcement/<int:announcement_id>/', DeleteAnnouncementView.as_view(), name='delete_announcement'),
    path('batch_delete_announcements/', BatchDeleteAnnouncementsView.as_view(), name='batch_delete_announcements'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

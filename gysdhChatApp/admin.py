from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User, Announcement, Message, FileDownloadLog, EmailTemplate,
    UserGroup, Notice, Tag, UserTag, SystemSettings
)

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('number', 'name', 'companyCode', 'email', 'is_admin', 'is_active', 'date_joined')
    list_filter = ('is_admin', 'is_active', 'can_publish_announcements', 'can_private_message', 'is_event_staff')
    search_fields = ('number', 'name', 'email', 'companyCode')
    ordering = ('-date_joined',)
    filter_horizontal = ()
    fieldsets = (
        (None, {'fields': ('number', 'password')}),
        ('Personal info', {'fields': ('name', 'companyCode', 'email')}),
        ('Permissions', {'fields': ('is_admin', 'is_active', 'can_publish_announcements', 'can_private_message', 'is_event_staff')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('number', 'name', 'companyCode', 'email', 'password1', 'password2'),
        }),
    )

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('content', 'publisher', 'timestamp')
    list_filter = ('timestamp', 'publisher')
    search_fields = ('content', 'publisher__name')
    ordering = ('-timestamp',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'content', 'timestamp', 'is_private', 'recipient')
    list_filter = ('timestamp', 'is_private', 'is_recalled', 'is_deleted')
    search_fields = ('content', 'sender__name', 'recipient__name')
    ordering = ('-timestamp',)

@admin.register(FileDownloadLog)
class FileDownloadLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_name', 'file_type', 'downloaded_at', 'ip_address')
    list_filter = ('file_type', 'downloaded_at', 'user')
    search_fields = ('user__name', 'file_name', 'ip_address')
    date_hierarchy = 'downloaded_at'
    readonly_fields = ('user', 'file_name', 'file_type', 'content_type', 'file_size', 
                      'source_id', 'downloaded_at', 'ip_address', 'user_agent')

@admin.register(UserGroup)
class UserGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('name',)

@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('content', 'publisher', 'is_active', 'timestamp')
    list_filter = ('is_active', 'timestamp', 'publisher')
    search_fields = ('content', 'publisher__name')
    ordering = ('-timestamp',)

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'color', 'description', 'created_by', 'created_at')
    search_fields = ('name', 'description', 'created_by__name')
    ordering = ('name',)

@admin.register(UserTag)
class UserTagAdmin(admin.ModelAdmin):
    list_display = ('user', 'tag', 'added_by', 'added_at')
    list_filter = ('tag', 'added_at')
    search_fields = ('user__name', 'tag__name', 'added_by__name')
    ordering = ('-added_at',)

@admin.register(SystemSettings)
class SystemSettingsAdmin(admin.ModelAdmin):
    list_display = ('chat_title', 'chat_area_title', 'email_host', 'updated_at', 'updated_by')
    readonly_fields = ('updated_at', 'updated_by')

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'subject', 'description', 'created_by', 'created_at', 'updated_at')
    search_fields = ('name', 'subject', 'description')
    list_filter = ('created_at', 'updated_at', 'created_by')
    readonly_fields = ('created_at', 'updated_at', 'created_by')
    ordering = ('name',)

    def save_model(self, request, obj, form, change):
        if not change:  # 如果是新建模板
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
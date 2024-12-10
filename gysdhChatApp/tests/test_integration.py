import pytest
from django.urls import reverse
from django.utils import timezone
from gysdhChatApp.models import Message, Announcement, Notice

@pytest.mark.django_db
class TestChatIntegration:
    def test_send_and_receive_message(self, client, test_user, test_admin_user):
        """测试发送和接收消息的完整流程"""
        # 登录用户
        client.force_login(test_user)
        
        # 发送消息
        message_data = {
            'content': '测试消息内容',
            'is_private': True,
            'recipient': test_admin_user.id
        }
        response = client.post(
            reverse('send_message'),
            message_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 验证消息已保存
        message = Message.objects.first()
        assert message.content == message_data['content']
        assert message.sender == test_user
        assert message.recipient == test_admin_user
        
        # 接收者查看消息
        client.force_login(test_admin_user)
        response = client.get(reverse('get_messages'))
        assert response.status_code == 200
        assert message_data['content'] in str(response.content)

@pytest.mark.django_db
class TestAnnouncementIntegration:
    def test_publish_and_view_announcement(self, client, test_admin_user):
        """测试发布和查看公告的完整流程"""
        # 登录管理员
        client.force_login(test_admin_user)
        
        # 发布公告
        announcement_data = {
            'content': '测试公告内容',
            'priority': 2,
            'is_sticky': True,
            'expires_at': (timezone.now() + timezone.timedelta(days=7)).isoformat()
        }
        response = client.post(
            reverse('publish_announcement'),
            announcement_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 验证公告已保存
        announcement = Announcement.objects.first()
        assert announcement.content == announcement_data['content']
        assert announcement.publisher == test_admin_user
        
        # 查看公告列表
        response = client.get(reverse('get_announcements'))
        assert response.status_code == 200
        assert announcement_data['content'] in str(response.content)

@pytest.mark.django_db
class TestUserManagementIntegration:
    def test_user_group_assignment(self, client, test_admin_user, test_user, test_user_group):
        """测试用户组分配的完整流程"""
        # 登录管理员
        client.force_login(test_admin_user)
        
        # 分配用户组
        group_data = {
            'user_id': test_user.id,
            'group_id': test_user_group.id
        }
        response = client.post(
            reverse('assign_user_group'),
            group_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 验证用户组已更新
        test_user.refresh_from_db()
        assert test_user.group == test_user_group

@pytest.mark.django_db
class TestNoticeIntegration:
    def test_publish_and_view_notice(self, client, test_admin_user):
        """测试发布和查看注意事项的完整流程"""
        # 登录管理员
        client.force_login(test_admin_user)
        
        # 发布注意事项
        notice_data = {
            'content': '测试注意事项内容'
        }
        response = client.post(
            reverse('publish_notice'),
            notice_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 验证注意事项已保存
        notice = Notice.objects.first()
        assert notice.content == notice_data['content']
        assert notice.publisher == test_admin_user
        
        # 查看注意事项列表
        response = client.get(reverse('get_notices'))
        assert response.status_code == 200
        assert notice_data['content'] in str(response.content)

@pytest.mark.django_db
class TestSystemSettingsIntegration:
    def test_update_and_view_settings(self, client, test_admin_user, test_system_settings):
        """测试更新和查看系统设置的完整流程"""
        # 登录管理员
        client.force_login(test_admin_user)
        
        # 更新系统设置
        settings_data = {
            'chat_title': '更新后的聊天室',
            'chat_area_title': '更新后的聊天区域',
            'email_host': 'smtp.updated.com'
        }
        response = client.post(
            reverse('update_system_settings'),
            settings_data,
            content_type='application/json'
        )
        assert response.status_code == 200
        
        # 验证设置已更新
        test_system_settings.refresh_from_db()
        assert test_system_settings.chat_title == settings_data['chat_title']
        assert test_system_settings.chat_area_title == settings_data['chat_area_title']
        assert test_system_settings.email_host == settings_data['email_host']

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from gysdhChatApp.models import (
    User, UserGroup, Announcement, Message, Notice, Tag, UserTag
)

class TestUserModel:
    def test_user_creation(self, test_user):
        """测试用户创建"""
        assert test_user.name == "测试用户"
        assert test_user.companyCode == "TEST01"
        assert test_user.email == "test@example.com"
        assert test_user.is_active
        assert not test_user.is_admin

    def test_user_str(self, test_user):
        """测试用户字符串表示"""
        assert str(test_user) == f"{test_user.name} ({test_user.number})"

    def test_user_number_unique(self, test_user):
        """测试用户编号唯一性"""
        User = type(test_user)
        with pytest.raises(ValidationError):
            user2 = User(
                name="另一个用户",
                companyCode="TEST02",
                email="test2@example.com",
                number=test_user.number
            )
            user2.full_clean()

class TestUserGroupModel:
    def test_group_creation(self, test_user_group):
        """测试用户组创建"""
        assert test_user_group.name == "测试组"
        assert test_user_group.description == "用于测试的用户组"

    def test_group_str(self, test_user_group):
        """测试用户组字符串表示"""
        assert str(test_user_group) == test_user_group.name

    def test_group_name_unique(self, test_user_group):
        """测试用户组名称唯一性"""
        with pytest.raises(ValidationError):
            group2 = UserGroup(name=test_user_group.name)
            group2.full_clean()

class TestAnnouncementModel:
    @pytest.fixture
    def test_announcement(self, test_admin_user):
        """创建测试公告"""
        return Announcement.objects.create(
            content="测试公告内容",
            publisher=test_admin_user,
            priority=2
        )

    def test_announcement_creation(self, test_announcement):
        """测试公告创建"""
        assert test_announcement.content == "测试公告内容"
        assert test_announcement.priority == 2
        assert not test_announcement.is_sticky

    def test_announcement_expiration(self, test_announcement):
        """测试公告过期功能"""
        assert not test_announcement.is_expired()
        
        test_announcement.expires_at = timezone.now() - timezone.timedelta(days=1)
        test_announcement.save()
        assert test_announcement.is_expired()

class TestMessageModel:
    @pytest.fixture
    def test_message(self, test_user, test_admin_user):
        """创建测试消息"""
        return Message.objects.create(
            sender=test_user,
            content="测试消息内容",
            recipient=test_admin_user,
            is_private=True
        )

    def test_message_creation(self, test_message):
        """测试消息创建"""
        assert test_message.content == "测试消息内容"
        assert test_message.is_private
        assert not test_message.is_recalled
        assert not test_message.is_deleted

    def test_message_recall(self, test_message):
        """测试消息撤回功能"""
        test_message.is_recalled = True
        test_message.recalled_at = timezone.now()
        test_message.save()
        assert test_message.is_recalled
        assert test_message.recalled_at is not None

class TestTagModel:
    def test_tag_creation(self, test_tag):
        """测试标签创建"""
        assert test_tag.name == "测试标签"
        assert test_tag.color == "#FF0000"
        assert test_tag.description == "用于测试的标签"

    def test_tag_str(self, test_tag):
        """测试标签字符串表示"""
        assert str(test_tag) == test_tag.name

    def test_tag_name_unique(self, test_tag, test_admin_user):
        """测试标签名称唯一性"""
        with pytest.raises(ValidationError):
            tag2 = Tag(
                name=test_tag.name,
                color="#00FF00",
                created_by=test_admin_user
            )
            tag2.full_clean()

class TestUserTagModel:
    @pytest.fixture
    def test_user_tag(self, test_user, test_tag, test_admin_user):
        """创建测试用户标签"""
        return UserTag.objects.create(
            user=test_user,
            tag=test_tag,
            added_by=test_admin_user
        )

    def test_user_tag_creation(self, test_user_tag):
        """测试用户标签创建"""
        assert test_user_tag.user.name == "测试用户"
        assert test_user_tag.tag.name == "测试标签"
        assert test_user_tag.added_by.name == "管理员"

    def test_user_tag_unique_together(self, test_user_tag):
        """测试用户标签唯一性约束"""
        with pytest.raises(ValidationError):
            user_tag2 = UserTag(
                user=test_user_tag.user,
                tag=test_user_tag.tag,
                added_by=test_user_tag.added_by
            )
            user_tag2.full_clean()

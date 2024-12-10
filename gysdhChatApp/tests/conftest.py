import pytest
from django.contrib.auth import get_user_model
from gysdhChatApp.models import UserGroup, Tag, SystemSettings

@pytest.fixture
def test_user_group(db):
    """创建测试用户组"""
    return UserGroup.objects.create(
        name="测试组",
        description="用于测试的用户组"
    )

@pytest.fixture
def test_user(db, test_user_group):
    """创建测试用户"""
    User = get_user_model()
    user = User.objects.create_user(
        name="测试用户",
        companyCode="TEST01",
        email="test@example.com",
        password="testpass123"
    )
    user.group = test_user_group
    user.save()
    return user

@pytest.fixture
def test_admin_user(db, test_user_group):
    """创建测试管理员用户"""
    User = get_user_model()
    admin = User.objects.create_superuser(
        name="管理员",
        companyCode="ADMIN1",
        email="admin@example.com",
        password="adminpass123"
    )
    admin.group = test_user_group
    admin.save()
    return admin

@pytest.fixture
def test_tag(db, test_admin_user):
    """创建测试标签"""
    return Tag.objects.create(
        name="测试标签",
        color="#FF0000",
        description="用于测试的标签",
        created_by=test_admin_user
    )

@pytest.fixture
def test_system_settings(db):
    """创建测试系统设置"""
    return SystemSettings.objects.create(
        chat_title="测试聊天室",
        chat_area_title="测试聊天区域",
        email_host="smtp.test.com",
        email_port=587,
        email_host_user="test@test.com",
        email_host_password="testpass"
    )

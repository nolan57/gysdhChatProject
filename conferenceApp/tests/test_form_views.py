from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta

from ..models.conference import Conference
from ..models.registration import RegistrationForm
from ..models.company import SupplierCompany

class FormViewsTest(TestCase):
    def setUp(self):
        """设置测试环境"""
        # 创建测试用户
        User = get_user_model()
        self.user = User.objects.create_user(
            name='Test User',
            companyCode='TEST01',
            email='test@example.com',
            password='testpass123'
        )
        # 设置用户权限
        self.user.is_admin = True
        self.user.save()
        
        # 创建测试公司
        self.company = SupplierCompany.objects.create(
            name='Test Company',
            code='TEST01',
            business_type='测试'
        )
        
        # 创建测试会议
        now = timezone.now()
        self.conference = Conference.objects.create(
            name='Test Conference',
            code='TEST001',
            description='Test Description',
            organizer='Test Organizer',
            start_date=now + timedelta(days=7),
            end_date=now + timedelta(days=8),
            registration_start=now,
            registration_end=now + timedelta(days=5),
            check_in_start=now + timedelta(days=7),
            check_in_end=now + timedelta(days=8),
            venue_name='Test Venue',
            venue_address='Test Address',
            max_participants=100,
            company_max_participants=10,
            contact_person='Test Contact',
            contact_phone='1234567890',
            contact_email='contact@test.com'
        )
        
        # 创建测试表单
        self.form = RegistrationForm.objects.create(
            name='Test Form',
            description='Test Form Description'
        )
        
        # 关联表单到会议
        self.conference.registration_form = self.form
        self.conference.save()
        
        # 创建测试客户端
        self.client = Client()
        
        # 登录用户 - 使用 number 作为登录字段
        login_successful = self.client.login(username=self.user.number, password='testpass123')
        if not login_successful:
            raise Exception('Failed to log in test user')

    def test_render_formio_view(self):
        """测试表单渲染视图"""
        # 设置表单为 Form.io 表单
        self.form.is_formio = True
        self.form.formio_schema = {
            'components': [
                {'type': 'textfield', 'key': 'name', 'label': '姓名'},
                {'type': 'email', 'key': 'email', 'label': '邮箱'}
            ]
        }
        self.form.save()
        
        # 访问表单渲染页面
        url = reverse('conference:render_formio', kwargs={'conference_id': self.conference.id})
        response = self.client.get(url)
        
        # 验证响应
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'conferenceApp/registration/formio_form.html')
        self.assertContains(response, '姓名')
        self.assertContains(response, '邮箱')
        self.assertContains(response, 'formio-container')

    def test_render_formio_invalid_form(self):
        """测试无效表单的情况"""
        # 访问表单渲染页面
        url = reverse('conference:render_formio', kwargs={'conference_id': self.conference.id})
        response = self.client.get(url)
        
        # 验证响应
        self.assertEqual(response.status_code, 400)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': '此表单不是 Form.io 表单'}
        )

    def test_render_formio_no_form(self):
        """测试会议没有关联表单的情况"""
        # 移除会议关联的表单
        self.conference.registration_form = None
        self.conference.save()
        
        # 访问表单渲染页面
        url = reverse('conference:render_formio', kwargs={'conference_id': self.conference.id})
        response = self.client.get(url)
        
        # 验证响应
        self.assertEqual(response.status_code, 404)
        self.assertJSONEqual(
            str(response.content, encoding='utf8'),
            {'error': '会议没有关联的表单'}
        )

from django.test import TestCase, Client
from django.urls import reverse
from gysdhChatApp.models import User

class LoginViewTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(number='123456', name='Test User', companyCode='ABC123')
        self.user.set_password('password')
        self.user.save()

    def test_login_view_post(self):
        response = self.client.post(reverse('login_view'), {'number': '123456'})
        self.assertEqual(response.status_code, 302)  # Expecting a redirect
        self.assertRedirects(response, reverse('chat_view', kwargs={'user_id': self.user.id}))

    def test_login_view_get(self):
        response = self.client.get(reverse('login_view'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'login.html')

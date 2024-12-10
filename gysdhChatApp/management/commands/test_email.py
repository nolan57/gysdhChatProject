from django.core.management.base import BaseCommand
from django.core.mail import send_mail, EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
import os

class Command(BaseCommand):
    help = '测试各种邮件发送功能'

    def handle(self, *args, **options):
        self.test_simple_email()
        self.test_html_email()
        self.test_attachment_email()
        self.test_private_message_notification()
        self.test_announcement_notification()

    def test_simple_email(self):
        """测试简单文本邮件"""
        try:
            send_mail(
                subject='测试普通文本邮件',
                message='这是一封测试邮件，用于验证基本的邮件发送功能。',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('普通文本邮件发送成功！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'普通文本邮件发送失败：{str(e)}'))

    def test_html_email(self):
        """测试HTML格式邮件"""
        try:
            html_content = """
            <html>
                <body>
                    <h1 style="color: #4CAF50;">HTML邮件测试</h1>
                    <p>这是一封<strong>HTML格式</strong>的测试邮件。</p>
                    <ul>
                        <li>支持HTML标签</li>
                        <li>支持样式</li>
                        <li>更好的排版效果</li>
                    </ul>
                    <p style="color: #666;">来自GYSDH Chat的测试邮件</p>
                </body>
            </html>
            """
            send_mail(
                subject='测试HTML邮件',
                message='这是一封HTML格式的测试邮件。',
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('HTML邮件发送成功！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'HTML邮件发送失败：{str(e)}'))

    def test_attachment_email(self):
        """测试带附件的邮件"""
        try:
            # 创建一个测试文件
            test_file_path = os.path.join(settings.BASE_DIR, 'test_attachment.txt')
            with open(test_file_path, 'w') as f:
                f.write('这是测试附件的内容。\n这是第二行内容。')

            # 创建邮件
            email = EmailMessage(
                subject='测试带附件的邮件',
                body='这是一封带附件的测试邮件。',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=['test@example.com'],
            )

            # 添加附件
            email.attach_file(test_file_path)
            email.send(fail_silently=False)

            # 清理测试文件
            os.remove(test_file_path)
            
            self.stdout.write(self.style.SUCCESS('带附件的邮件发送成功！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'带附件的邮件发送失败：{str(e)}'))

    def test_private_message_notification(self):
        """测试私信通知邮件"""
        try:
            subject = '[GYSDH Chat] 新私信提醒'
            html_content = """
            <html>
                <body>
                    <h2 style="color: #2196F3;">您收到一条新的私信</h2>
                    <div style="border-left: 4px solid #2196F3; padding-left: 10px; margin: 10px 0;">
                        <p><strong>发送者：</strong>张三</p>
                        <p><strong>发送时间：</strong>2024-01-01 12:00:00</p>
                        <p><strong>消息内容：</strong></p>
                        <p style="background-color: #f5f5f5; padding: 10px;">
                            这是一条测试私信内容。希望你今天过得愉快！
                        </p>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        此邮件由系统自动发送，请勿直接回复。
                    </p>
                </body>
            </html>
            """
            send_mail(
                subject=subject,
                message='您收到一条新的私信',
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('私信通知邮件发送成功！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'私信通知邮件发送失败：{str(e)}'))

    def test_announcement_notification(self):
        """测试公告通知邮件"""
        try:
            subject = '[GYSDH Chat] 新公告'
            html_content = """
            <html>
                <body>
                    <h2 style="color: #FF5722;">系统公告</h2>
                    <div style="border-left: 4px solid #FF5722; padding-left: 10px; margin: 10px 0;">
                        <p><strong>发布时间：</strong>2024-01-01 12:00:00</p>
                        <p><strong>公告内容：</strong></p>
                        <p style="background-color: #fff3e0; padding: 10px;">
                            这是一条测试公告内容。系统将于本周日进行例行维护，
                            维护时间为2024年1月7日凌晨2:00-4:00。
                            维护期间系统将暂停服务，请您提前做好相关安排。
                            感谢您的理解与支持！
                        </p>
                    </div>
                    <p style="color: #666; font-size: 12px;">
                        此邮件由系统自动发送，请勿直接回复。
                    </p>
                </body>
            </html>
            """
            send_mail(
                subject=subject,
                message='系统发布了新公告',
                html_message=html_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=['test@example.com'],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS('公告通知邮件发送成功！'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'公告通知邮件发送失败：{str(e)}'))

import pandas as pd
from django.http import HttpResponse
from ..models import User, Message, Announcement
from typing import List, Optional
import datetime
import os

class ExportService:
    @staticmethod
    def _get_export_filename(prefix: str) -> str:
        """生成导出文件名"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.xlsx"

    @classmethod
    def export_users(cls, queryset=None) -> HttpResponse:
        """导出用户数据"""
        if queryset is None:
            queryset = User.objects.all()

        # 准备数据
        data = []
        for user in queryset:
            data.append({
                '账号': user.number,
                '用户名': user.name,
                '密码': user.original_password,  # 现在会返回解密后的原始密码
                '用户代码': user.number,
                '公司代码': user.companyCode,
                '邮箱': user.email,
                '是否管理员': '是' if user.is_admin else '否',
                '可发布公告': '是' if user.can_publish_announcements else '否',
                '可发送私信': '是' if user.can_private_message else '否',
                '是否工作人员': '是' if user.is_event_staff else '否',
                '创建时间': user.date_joined.strftime('%Y-%m-%d %H:%M:%S'),
                '最后登录': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else '',
            })

        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建响应
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{cls._get_export_filename("users")}"'
        
        # 写入Excel
        df.to_excel(response, index=False, engine='openpyxl')
        return response

    @classmethod
    def export_messages(cls, queryset=None, start_date: Optional[datetime.date] = None,
                       end_date: Optional[datetime.date] = None) -> HttpResponse:
        """导出聊天记录"""
        if queryset is None:
            queryset = Message.objects.all()

        # 日期过滤
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)

        # 准备数据
        data = []
        for message in queryset.select_related('sender', 'recipient', 'reply_to'):
            data.append({
                '消息ID': message.id,
                '发送时间': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                '发送者': message.sender.name,
                '发送者账号': message.sender.number,
                '接收者': message.recipient.name if message.recipient else '所有人',
                '接收者账号': message.recipient.number if message.recipient else '',
                '消息内容': message.content,
                '是否私信': '是' if message.is_private else '否',
                '回复消息ID': message.reply_to.id if message.reply_to else '',
                '回复对象': message.reply_to.sender.name if message.reply_to else '',
                '文件名': os.path.basename(message.file.name) if message.file else '',
            })

        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建响应
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{cls._get_export_filename("messages")}"'
        
        # 写入Excel
        df.to_excel(response, index=False, engine='openpyxl')
        return response

    @classmethod
    def export_announcements(cls, queryset=None, start_date: Optional[datetime.date] = None,
                           end_date: Optional[datetime.date] = None) -> HttpResponse:
        """导出公告"""
        if queryset is None:
            queryset = Announcement.objects.all()

        # 日期过滤
        if start_date:
            queryset = queryset.filter(timestamp__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__date__lte=end_date)

        # 准备数据
        data = []
        for announcement in queryset.select_related('publisher'):
            has_file = bool(announcement.file)
            data.append({
                '公告ID': announcement.id,
                '发布时间': announcement.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                '发布者': announcement.publisher.name if announcement.publisher else '未知',
                '发布者账号': announcement.publisher.number if announcement.publisher else '未知',
                '公告内容': announcement.content,
                '附件': '有' if has_file else '无',
                '附件名称': announcement.file.name if has_file else '',
            })

        # 创建DataFrame
        df = pd.DataFrame(data)
        
        # 创建响应
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="{cls._get_export_filename("announcements")}"'
        
        # 写入Excel
        df.to_excel(response, index=False, engine='openpyxl')
        return response

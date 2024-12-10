from django.views import View
from django.shortcuts import render, redirect
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
from django.core.files.storage import FileSystemStorage
from django.core.paginator import Paginator

from ..utils import import_users_from_excel
from ..models import User

class ImportUsersView(LoginRequiredMixin, View):
    template_name = 'admin/import_users.html'
    
    def get(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限访问此页面')
            return redirect('chat_view', request.user.id)
            
        # 获取用户列表并分页
        users = User.objects.all().order_by('-date_joined')
        paginator = Paginator(users, 10)  # 每页显示10条
        page_number = request.GET.get('page', 1)
        users_page = paginator.get_page(page_number)
        
        context = {
            'users': users_page,
        }
        return render(request, self.template_name, context)
    
    def post(self, request):
        if not request.user.is_admin:
            messages.error(request, '您没有权限执行此操作')
            return redirect('chat_view', request.user.id)
            
        if 'file' not in request.FILES:
            messages.error(request, '请选择要上传的Excel文件')
            return render(request, self.template_name)
            
        excel_file = request.FILES['file']
        
        # 检查文件类型
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, '请上传Excel文件（.xlsx或.xls格式）')
            return render(request, self.template_name)
            
        # 保存上传的文件
        fs = FileSystemStorage(location='temp')
        filename = fs.save(excel_file.name, excel_file)
        file_path = os.path.join('temp', filename)
        
        try:
            # 导入用户
            results = import_users_from_excel(file_path)
            
            if results['success'] > 0:
                success_msg = f'成功导入 {results["success"]} 个用户。'
                if not results['email_failed']:
                    success_msg += '所有用户都已收到账号信息邮件。'
                else:
                    success_msg += f'{len(results["email_failed"])} 个用户的邮件发送失败。'
                messages.success(request, success_msg)
            
            if results['failed'] > 0:
                for error in results['errors']:
                    messages.error(request, error)
            
            # 如果有邮件发送失败的用户，显示他们的账号信息
            if results['email_failed']:
                email_failed_msg = '以下用户的邮件发送失败，请手动告知他们的账号信息：\n'
                for user in results['email_failed']:
                    email_failed_msg += f'\n用户名：{user["name"]}'
                    email_failed_msg += f'\n账号：{user["number"]}'
                    email_failed_msg += f'\n密码：{user["password"]}\n'
                messages.warning(request, email_failed_msg)
                    
        except Exception as e:
            messages.error(request, f'导入失败：{str(e)}')
            
        finally:
            # 清理临时文件
            if os.path.exists(file_path):
                os.remove(file_path)
                
        # 获取最新的用户列表
        users = User.objects.all().order_by('-date_joined')
        paginator = Paginator(users, 10)
        users_page = paginator.get_page(1)
        
        context = {
            'users': users_page,
            'results': results if 'results' in locals() else None
        }
        return render(request, self.template_name, context)

from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    """要求用户必须是管理员的Mixin"""
    
    def test_func(self):
        """测试用户是否是管理员"""
        return self.request.user.is_staff
    
    def handle_no_permission(self):
        """处理没有权限的情况"""
        if not self.request.user.is_authenticated:
            return redirect('login')
        messages.error(self.request, '您没有权限访问此页面！')
        return redirect('chat_view', user_id=self.request.user.id)

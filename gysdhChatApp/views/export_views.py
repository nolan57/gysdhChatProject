from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import render
from ..services.export_service import ExportService
from datetime import datetime, date

class ExportBaseView(LoginRequiredMixin, View):
    def get_date_range(self):
        """从请求中获取日期范围"""
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
            
        return start_date, end_date

class ExportManagementView(LoginRequiredMixin, View):
    template_name = 'export_management.html'

    def get(self, request):
        if not request.user.is_admin:
            return HttpResponseForbidden("没有导出权限")
        return render(request, self.template_name, {'today': date.today()})

class ExportUsersView(ExportBaseView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden("没有导出权限")
        return ExportService.export_users()

class ExportMessagesView(ExportBaseView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden("没有导出权限")
        
        start_date, end_date = self.get_date_range()
        return ExportService.export_messages(start_date=start_date, end_date=end_date)

class ExportAnnouncementsView(ExportBaseView):
    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return HttpResponseForbidden("没有导出权限")
        
        start_date, end_date = self.get_date_range()
        return ExportService.export_announcements(start_date=start_date, end_date=end_date)

import os
import mimetypes
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import get_object_or_404, render
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from ..models import Message, Announcement, FileDownloadLog

class FileDownloadMixin:
    @staticmethod
    def download_file(file_field, request, source_type, source_id):
        try:
            if file_field:
                file_path = file_field.path
            else:
                raise ObjectDoesNotExist

            with open(file_path, 'rb') as fh:
                content_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
                file_content = fh.read()
                
                # 记录下载信息
                FileDownloadLog.objects.create(
                    user=request.user,
                    file_name=os.path.basename(file_path),
                    file_type=source_type,
                    content_type=content_type,
                    file_size=len(file_content),
                    source_id=source_id,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT')
                )
                
                response = HttpResponse(file_content, content_type=content_type)
                response['Content-Disposition'] = 'attachment; filename=' + os.path.basename(file_path)
                return response
        except ObjectDoesNotExist:
            return HttpResponse('File not found', status=404)
        except Exception as e:
            return HttpResponse(str(e), status=500)

@login_required
def download_message_file(request, file_id):
    message = get_object_or_404(Message, id=file_id)
    return FileDownloadMixin.download_file(message.file, request, 'message', file_id)

@login_required
def download_announcement_file(request, file_id):
    announcement = get_object_or_404(Announcement, id=file_id)
    return FileDownloadMixin.download_file(announcement.file, request, 'announcement', file_id)

@login_required
def download_file(request, file_type, file_id):
    """统一的文件下载处理函数"""
    if file_type == 'message':
        return download_message_file(request, file_id)
    elif file_type == 'announcement':
        return download_announcement_file(request, file_id)
    else:
        return HttpResponse('Invalid file type', status=400)

@staff_member_required
def download_logs(request):
    """查看文件下载记录"""
    logs = FileDownloadLog.objects.all().order_by('-downloaded_at')
    return render(request, 'download_logs.html', {
        'logs': logs,
        'title': '文件下载记录',
    })

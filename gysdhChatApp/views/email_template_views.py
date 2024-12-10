from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponseRedirect
from django.template import Template, Context
from ..models import EmailTemplate
from ..forms.email_template_forms import EmailTemplateForm
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from celery import shared_task

class EmailTemplateListView(LoginRequiredMixin, ListView):
    model = EmailTemplate
    template_name = 'email/template_list.html'
    context_object_name = 'templates'
    paginate_by = 10

    def get_queryset(self):
        queryset = EmailTemplate.objects.all().order_by('-created_at')
        
        # 应用搜索过滤
        name = self.request.GET.get('name')
        subject = self.request.GET.get('subject')
        
        if name:
            queryset = queryset.filter(name__icontains=name)
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filters'] = {
            'name': self.request.GET.get('name', ''),
            'subject': self.request.GET.get('subject', '')
        }
        return context

class EmailTemplateCreateView(LoginRequiredMixin, CreateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'email/template_form.html'
    success_url = reverse_lazy('template_list')
    
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        messages.success(self.request, '邮件模板创建成功')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单验证失败，请检查输入')
        return super().form_invalid(form)

class EmailTemplateUpdateView(LoginRequiredMixin, UpdateView):
    model = EmailTemplate
    form_class = EmailTemplateForm
    template_name = 'email/template_form.html'
    success_url = reverse_lazy('template_list')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, '邮件模板更新成功')
        return response

    def form_invalid(self, form):
        messages.error(self.request, '表单验证失败，请检查输入')
        return super().form_invalid(form)

class EmailTemplateDeleteView(LoginRequiredMixin, DeleteView):
    model = EmailTemplate
    success_url = reverse_lazy('template_list')
    
    def delete(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
            self.object.delete()
            messages.success(request, '邮件模板删除成功')
            return HttpResponseRedirect(self.get_success_url())
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
            return HttpResponseRedirect(self.get_success_url())
    
    def get(self, request, *args, **kwargs):
        return self.delete(request, *args, **kwargs)

class EmailTemplatePreviewView(LoginRequiredMixin, DetailView):
    model = EmailTemplate
    template_name = 'email/template_preview.html'
    context_object_name = 'template'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        template = self.get_object()
        
        # 获取示例变量
        variables = template.variables or {}
        sample_data = {}
        for key, description in variables.items():
            if isinstance(description, str):
                sample_data[key] = f"示例{description}"
            else:
                sample_data[key] = f"示例值"
        
        # 渲染模板
        try:
            t = Template(template.content)
            c = Context(sample_data)
            rendered_content = t.render(c)
            context['rendered_content'] = rendered_content
            context['error'] = None
        except Exception as e:
            context['rendered_content'] = ""
            context['error'] = str(e)
        
        return context

@shared_task
def send_batch_emails(template_id, user_ids, subject, sender=None):
    """
    Celery任务：批量发送邮件
    """
    template = EmailTemplate.objects.get(id=template_id)
    users = get_user_model().objects.filter(id__in=user_ids)
    
    for user in users:
        # 准备模板变量
        context = {
            'user': {
                'username': user.username,
                'email': user.email,
                'number': user.number,
                # 添加其他需要的用户属性
            }
        }
        
        # 渲染邮件内容
        content_template = Template(template.content)
        rendered_content = content_template.render(Context(context))
        
        # 发送邮件
        try:
            send_mail(
                subject or template.subject,
                rendered_content,
                sender or settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception as e:
            print(f"Failed to send email to {user.email}: {str(e)}")

class BatchEmailSendView(LoginRequiredMixin, View):
    """
    批量发送邮件视图
    """
    def post(self, request, *args, **kwargs):
        # 打印原始请求数据
        print("Raw POST data:", dict(request.POST))
        print("Raw POST items:", list(request.POST.items()))
        
        template_id = request.POST.get('template_id')
        user_ids = request.POST.getlist('user_ids[]')  # 使用getlist来获取数组
        custom_subject = request.POST.get('subject')
        
        print(f"Processed data: template_id={template_id}, user_ids={user_ids}, subject={custom_subject}")
        
        if not template_id:
            print("Error: No template_id provided")
            return JsonResponse({'status': 'error', 'message': '请选择邮件模板'}, status=400)
            
        if not user_ids:
            print("Error: No user_ids provided")
            return JsonResponse({'status': 'error', 'message': '请选择收件人'}, status=400)
            
        try:
            # 验证模板是否存在
            template = EmailTemplate.objects.get(id=template_id)
            print(f"Found template: {template.name}")
            
            # 验证用户是否存在
            User = get_user_model()
            users = User.objects.filter(id__in=user_ids)
            if not users.exists():
                print(f"Error: No users found for ids: {user_ids}")
                return JsonResponse({'status': 'error', 'message': '未找到选中的用户'}, status=400)
            
            print(f"Found {users.count()} users")
            
            # 异步发送邮件
            send_batch_emails.delay(
                template_id=template_id,
                user_ids=user_ids,
                subject=custom_subject
            )
            
            success_message = f'正在给{len(user_ids)}位用户发送邮件，请稍后查看结果'
            messages.success(request, success_message)
            print(f"Success: {success_message}")
            return JsonResponse({'status': 'success', 'message': success_message})
            
        except EmailTemplate.DoesNotExist:
            error_message = f'邮件模板不存在 (ID: {template_id})'
            print(f"Error: {error_message}")
            return JsonResponse({'status': 'error', 'message': error_message}, status=400)
            
        except Exception as e:
            error_message = f'发送失败: {str(e)}'
            print(f"Error in BatchEmailSendView: {error_message}")
            print(f"Exception type: {type(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            return JsonResponse({'status': 'error', 'message': error_message}, status=500)

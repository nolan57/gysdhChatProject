from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic import ListView
from django.views import View
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from ..models import User, UserGroup, Tag, UserTag, EmailTemplate
from ..forms.user_forms import UserCreationForm, UserUpdateForm, UserGroupForm
import random
import string
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from ..services.email_service import send_user_credentials_email
from django.http import JsonResponse

def generate_random_password(length=10):
    """Generate a random password with letters, digits and special characters."""
    characters = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(random.choice(characters) for _ in range(length))

class AdminRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_admin

class CreateUserView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = User
    form_class = UserCreationForm
    template_name = 'user/create_user.html'
    success_url = reverse_lazy('chat_view', kwargs={'user_id': 1})  # 默认返回到第一个用户的聊天页面

    def form_valid(self, form):
        # 创建用户但不保存到数据库
        user = form.save(commit=False)
        # 生成随机密码
        password = generate_random_password()
        user.original_password = password
        user.set_password(password)
        user.save()
        
        # 发送邮件通知
        if send_user_credentials_email(user, password, is_new=True):
            messages.success(self.request, 
                f'用户创建成功！账号信息已发送至用户邮箱。\n'
                f'用户名：{user.number}'
            )
        else:
            messages.success(self.request, 
                f'用户创建成功！但邮件发送失败，请手动告知用户账号信息：\n'
                f'用户名：{user.number}\n'
                f'密码：{password}'
            )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '用户创建失败，请检查输入信息。')
        return super().form_invalid(form)

class UserListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = User
    template_name = 'user/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).prefetch_related('user_tags__tag')
        
        # 按用户代码筛选
        number = self.request.GET.get('number')
        if number:
            queryset = queryset.filter(number__icontains=number)
        
        # 按姓名筛选
        name = self.request.GET.get('name')
        if name:
            queryset = queryset.filter(name__icontains=name)
        
        # 按角色筛选
        role = self.request.GET.get('role')
        if role == 'admin':
            queryset = queryset.filter(is_admin=True)
        elif role == 'staff':
            queryset = queryset.filter(is_event_staff=True, is_admin=False)
        elif role == 'normal':
            queryset = queryset.filter(is_event_staff=False, is_admin=False)
        
        # 按标签筛选
        tag_ids = self.request.GET.getlist('tags')
        if tag_ids:
            # 使用Q对象构建查询条件，要求用户拥有所有选中的标签
            from django.db.models import Q
            for tag_id in tag_ids:
                queryset = queryset.filter(user_tags__tag_id=tag_id)
        
        # 按注册时间范围筛选
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        if start_date:
            queryset = queryset.filter(date_joined__gte=start_date)
        if end_date:
            queryset = queryset.filter(date_joined__lte=end_date)
        
        return queryset.order_by('-date_joined').distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # 添加所有用户组到上下文
        context['groups'] = UserGroup.objects.all()
        # 添加所有标签到上下文
        context['all_tags'] = Tag.objects.all()
        # 添加邮件模板到上下文
        context['email_templates'] = EmailTemplate.objects.all().order_by('-created_at')
        # 添加筛选参数到上下文
        context['filters'] = {
            'number': self.request.GET.get('number', ''),
            'name': self.request.GET.get('name', ''),
            'role': self.request.GET.get('role', ''),
            'start_date': self.request.GET.get('start_date', ''),
            'end_date': self.request.GET.get('end_date', ''),
            'tags': self.request.GET.getlist('tags', [])
        }
        return context

class UpdateUserView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = 'user/update_user.html'
    success_url = reverse_lazy('user_list')
    pk_url_kwarg = 'user_id'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['user_to_edit'] = user
        return context

    def form_valid(self, form):
        user = form.save(commit=False)
        # 防止管理员取消自己的管理员权限
        if user == self.request.user and not form.cleaned_data['is_admin']:
            messages.error(self.request, '不能取消自己的管理员权限')
            return self.form_invalid(form)
        user.save()

        # 发送邮件通知
        if send_user_credentials_email(user, is_new=False, is_reset=False):
            messages.success(self.request, f'用户 {user.name} 的信息已更新，通知邮件已发送')
        else:
            messages.success(self.request, f'用户 {user.name} 的信息已更新，但邮件发送失败')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '更新失败，请检查输入信息')
        return super().form_invalid(form)

class DeleteUserView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        if user.id == request.user.id:
            messages.error(request, '不能删除自己的账号')
            return redirect('user_list')
        
        try:
            user.delete()
            messages.success(request, f'用户 {user.name} 已成功删除')
        except Exception as e:
            messages.error(request, f'删除用户时出错：{str(e)}')
        
        return redirect('user_list')

class ResetPasswordView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        # 生成随机密码
        new_password = generate_random_password()
        user.set_password(new_password)
        user.save()

        # 发送邮件通知
        if send_user_credentials_email(user, new_password, is_new=False, is_reset=True):
            messages.success(request, f'用户 {user.name} 的密码已重置，新密码已发送至用户邮箱')
        else:
            messages.success(request, f'用户 {user.name} 的密码已重置为：{new_password}，但邮件发送失败')
        return redirect('user_list')

class UserGroupListView(LoginRequiredMixin, AdminRequiredMixin, ListView):
    model = UserGroup
    template_name = 'user/group_list.html'
    context_object_name = 'groups'
    paginate_by = 10

class CreateUserGroupView(LoginRequiredMixin, AdminRequiredMixin, CreateView):
    model = UserGroup
    form_class = UserGroupForm
    template_name = 'user/group_form.html'
    success_url = reverse_lazy('group_list')

    def form_valid(self, form):
        messages.success(self.request, '用户组创建成功！')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '用户组创建失败，请检查输入信息。')
        return super().form_invalid(form)

class UpdateUserGroupView(LoginRequiredMixin, AdminRequiredMixin, UpdateView):
    model = UserGroup
    form_class = UserGroupForm
    template_name = 'user/group_form.html'
    success_url = reverse_lazy('group_list')
    pk_url_kwarg = 'group_id'

    def form_valid(self, form):
        messages.success(self.request, '用户组更新成功！')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, '用户组更新失败，请检查输入信息。')
        return super().form_invalid(form)

class DeleteUserGroupView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, group_id):
        group = get_object_or_404(UserGroup, id=group_id)
        try:
            group.delete()
            messages.success(request, '用户组删除成功！')
        except Exception as e:
            messages.error(request, f'用户组删除失败：{str(e)}')
        return redirect('group_list')

class UserGroupDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'user/group_detail.html'

    def get(self, request, group_id):
        group = get_object_or_404(UserGroup, id=group_id)
        users_in_group = User.objects.filter(group=group)
        available_users = User.objects.filter(group__isnull=True)
        
        context = {
            'group': group,
            'users_in_group': users_in_group,
            'available_users': available_users
        }
        return render(request, self.template_name, context)

    def post(self, request, group_id):
        group = get_object_or_404(UserGroup, id=group_id)
        action = request.POST.get('action')
        user_ids = request.POST.getlist('user_ids[]')
        users = User.objects.filter(id__in=user_ids)

        if action == 'add':
            users.update(group=group)
            messages.success(request, f'已将选中的用户添加到用户组 {group.name}')
        elif action == 'remove':
            users.update(group=None)
            messages.success(request, f'已将选中的用户从用户组 {group.name} 移除')
        
        return redirect('group_detail', group_id=group_id)

class BatchAssignGroupView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        user_ids_str = request.POST.get('user_ids[]', '')
        group_id = request.POST.get('group_id')
        
        if not user_ids_str or not group_id:
            messages.error(request, '请选择用户和用户组')
            return redirect('user_list')
        
        try:
            # 将逗号分隔的字符串转换为整数列表
            user_ids = [int(id) for id in user_ids_str.split(',')]
            group = get_object_or_404(UserGroup, id=group_id)
            
            # 获取选中的用户
            users = User.objects.filter(id__in=user_ids)
            if not users:
                messages.error(request, '未找到选中的用户')
                return redirect('user_list')
            
            # 将用户添加到用户组
            for user in users:
                user.group = group
                user.save()
            
            messages.success(request, f'已成功将 {len(users)} 个用户添加到 {group.name} 用户组')
        except ValueError:
            messages.error(request, '无效的用户或用户组ID')
        except UserGroup.DoesNotExist:
            messages.error(request, '未找到指定的用户组')
        except Exception as e:
            messages.error(request, f'操作失败：{str(e)}')
        
        return redirect('user_list')

class BatchDeleteUsersView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        user_ids_str = request.POST.get('user_ids[]', '')
        
        if not user_ids_str:
            messages.error(request, '请选择要删除的用户')
            return redirect('user_list')
        
        try:
            # 将逗号分隔的字符串转换为整数列表
            user_ids = [int(id) for id in user_ids_str.split(',')]
            
            # 检查是否试图删除当前用户
            if request.user.id in user_ids:
                messages.error(request, '不能删除自己的账号')
                # 从删除列表中移除当前用户
                user_ids.remove(request.user.id)
                if not user_ids:  # 如果只选择了当前用户
                    return redirect('user_list')
            
            # 获取要删除的用户
            users = User.objects.filter(id__in=user_ids)
            if not users:
                messages.error(request, '未找到要删除的用户')
                return redirect('user_list')
            
            # 记录要删除的用户名，用于显示在成功消息中
            user_names = [user.name for user in users]
            deleted_count = users.count()
            
            # 删除用户
            users.delete()
            
            messages.success(request, f'已成功删除 {deleted_count} 个用户：{", ".join(user_names)}')
        except ValueError:
            messages.error(request, '无效的用户ID')
        except Exception as e:
            messages.error(request, f'删除失败：{str(e)}')
        
        return redirect('user_list')

class DeleteUsersByGroupView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request, group_id):
        group = get_object_or_404(UserGroup, id=group_id)
        
        try:
            # 获取组内用户，但排除当前登录用户
            users_to_delete = User.objects.filter(group=group).exclude(id=request.user.id)
            user_names = [user.name for user in users_to_delete]
            
            if not users_to_delete.exists():
                messages.warning(request, '该组内没有可删除的用户')
                return redirect('group_detail', group_id=group_id)
            
            # 执行删除
            delete_count = users_to_delete.delete()[0]
            
            if delete_count > 0:
                messages.success(request, f'成功删除用户组 {group.name} 中的 {delete_count} 个用户：{", ".join(user_names)}')
            else:
                messages.warning(request, '没有删除任何用户')
        except Exception as e:
            messages.error(request, f'删除用户时出错：{str(e)}')
        
        return redirect('group_detail', group_id=group_id)

class UserDetailView(LoginRequiredMixin, AdminRequiredMixin, View):
    template_name = 'user/user_detail.html'

    def get(self, request, user_id):
        user = get_object_or_404(User, id=user_id)
        return render(request, self.template_name, {
            'user': user,
            'user_tags': user.user_tags.all(),
        })

class BatchAssignTagsView(LoginRequiredMixin, AdminRequiredMixin, View):
    def post(self, request):
        user_ids = request.POST.getlist('user_ids[]')
        tag_ids = request.POST.getlist('tag_ids[]')
        action = request.POST.get('action', 'add')  # 'add', 'remove' or 'remove_all'
        
        if not user_ids:
            messages.error(request, '请选择用户')
            return JsonResponse({'status': 'error', 'message': '请选择用户'})
        
        try:
            users = User.objects.filter(id__in=user_ids)
            
            if action == 'add':
                if not tag_ids:
                    messages.error(request, '请选择标签')
                    return JsonResponse({'status': 'error', 'message': '请选择标签'})
                tags = Tag.objects.filter(id__in=tag_ids)
                # 添加标签
                for user in users:
                    for tag in tags:
                        UserTag.objects.get_or_create(user=user, tag=tag)
                messages.success(request, '已成功添加所选标签')
            elif action == 'remove_all':
                # 移除所有标签
                UserTag.objects.filter(user__in=users).delete()
                messages.success(request, '已成功移除所有标签')
            else:
                # 移除特定标签
                if not tag_ids:
                    messages.error(request, '请选择标签')
                    return JsonResponse({'status': 'error', 'message': '请选择标签'})
                tags = Tag.objects.filter(id__in=tag_ids)
                UserTag.objects.filter(user__in=users, tag__in=tags).delete()
                messages.success(request, '已成功移除所选标签')
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            messages.error(request, f'操作失败：{str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)})

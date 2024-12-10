from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction

from ..models.conference import Conference
from ..models.registration import Registration
from ..models.company import ContactPerson
from ..models.participant import Participant

from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q

from ..forms import ConferenceForm, ContactFormSet

from gysdhChatApp.models import Notice, Tag, UserGroup

class DashboardView(LoginRequiredMixin, View):
    """仪表盘视图"""
    template_name = 'conferenceApp/dashboard.html'

    def get(self, request, *args, **kwargs):
        context = {}
        
        # 获取最近的会议
        if request.user.is_staff:
            # 管理员可以看到所有会议
            recent_conferences = Conference.objects.all().order_by('-start_date')[:5]
        else:
            # 普通用户只能看到公开的会议
            recent_conferences = Conference.objects.filter(
                Q(is_public=True) | Q(participants=request.user)
            ).distinct().order_by('-start_date')[:5]

        context.update({
            'recent_conferences': recent_conferences,
        })
        
        return render(request, self.template_name, context)

class ConferenceListView(LoginRequiredMixin, ListView):
    """会议列表视图"""
    model = Conference
    template_name = 'conferenceApp/conference_list.html'
    context_object_name = 'conferences'
    login_url = 'login'

    def get_queryset(self):
        """获取会议列表，根据用户权限过滤"""
        if self.request.user.is_staff:
            return Conference.objects.all().order_by('-created_at')
        return Conference.objects.filter(is_public=True).order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '会议管理'
        return context

class ConferenceCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = Conference
    form_class = ConferenceForm
    template_name = 'conferenceApp/conference_form.html'
    success_url = reverse_lazy('conference:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '添加会议'
        context['submit_text'] = '创建会议'
        if self.request.POST:
            context['contact_formset'] = ContactFormSet(self.request.POST, instance=self.object)
        else:
            context['contact_formset'] = ContactFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        with transaction.atomic():
            self.object = form.save()
            if contact_formset.is_valid():
                contact_formset.instance = self.object
                contact_formset.save()
            else:
                return self.form_invalid(form)
        messages.success(self.request, '会议创建成功！')
        return super().form_valid(form)

class ConferenceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Conference
    form_class = ConferenceForm
    template_name = 'conferenceApp/conference_form.html'
    success_url = reverse_lazy('conference:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '编辑会议'
        context['submit_text'] = '保存修改'
        if self.request.POST:
            context['contact_formset'] = ContactFormSet(self.request.POST, instance=self.object)
        else:
            context['contact_formset'] = ContactFormSet(instance=self.object)
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        contact_formset = context['contact_formset']
        with transaction.atomic():
            self.object = form.save()
            if contact_formset.is_valid():
                contact_formset.instance = self.object
                contact_formset.save()
            else:
                return self.form_invalid(form)
        messages.success(self.request, '会议更新成功！')
        return super().form_valid(form)

class ConferenceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Conference
    template_name = 'conferenceApp/conference_confirm_delete.html'
    success_url = reverse_lazy('conference:list')
    
    def test_func(self):
        return self.request.user.is_staff
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = '删除会议'
        return context
    
    def delete(self, request, *args, **kwargs):
        messages.success(self.request, '会议已删除！')
        return super().delete(request, *args, **kwargs)

class ConferenceManagementView(LoginRequiredMixin, UserPassesTestMixin, View):
    """会议管理视图"""
    template_name = 'conferenceApp/conference_management.html'

    def test_func(self):
        return self.request.user.is_staff

    def get(self, request, *args, **kwargs):
        # 获取所有会议并按创建时间倒序排列
        conferences = Conference.objects.all().order_by('-created_at')
        return render(request, self.template_name, {'conferences': conferences})

@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def dashboard_view(request):
    
    return render(request, 'conferenceApp/dashboard.html')

@login_required
def conference_detail(request, pk):
    """会议详情视图"""
    conference = get_object_or_404(Conference, pk=pk)
    
    # 获取报名状态
    registration_status = {
        'is_registration_period': conference.status == 'registration',
        'company_spaces_left': None,
        'company_limit_reached': False
    }
    
    # 检查是否可以报名 - 只要是报名期间且不是管理员就可以看到报名按钮
    can_register = request.user.is_authenticated and not request.user.is_admin and conference.status == 'registration'
    
    # 获取当前用户公司的报名情况
    if request.user.is_authenticated:
        company_participants = Registration.objects.filter(
            conference=conference,
            participant__company__code=request.user.companyCode,
            status__in=['pending', 'confirmed']
        ).count()
        registration_status['company_spaces_left'] = conference.company_max_participants - company_participants
    
    context = {
        'conference': conference,
        'can_register': can_register,
        'registration_status': registration_status,
    }
    
    return render(request, 'conferenceApp/conference_detail.html', context)

@login_required
def conference_create(request):
    if not request.user.is_staff:
        return HttpResponseForbidden("您没有权限执行此操作")
        
    if request.method == 'POST':
        form = ConferenceForm(request.POST)
        if form.is_valid():
            conference = form.save()
            messages.success(request, '会议创建成功！')
            return redirect('conference:list')
    else:
        form = ConferenceForm()
    
    return render(request, 'conferenceApp/conference_form.html', {
        'form': form,
        'title': '创建会议',
        'submit_text': '创建会议'
    })

@login_required
def conference_edit(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("您没有权限执行此操作")
        
    conference = get_object_or_404(Conference, pk=pk)
    if request.method == 'POST':
        form = ConferenceForm(request.POST, instance=conference)
        if form.is_valid():
            conference = form.save()
            messages.success(request, '会议更新成功！')
            return redirect('conference:list')
    else:
        form = ConferenceForm(instance=conference)
    
    return render(request, 'conferenceApp/conference_form.html', {
        'form': form,
        'title': '编辑会议',
        'submit_text': '更新会议'
    })

@login_required
def conference_delete(request, pk):
    if not request.user.is_staff:
        return HttpResponseForbidden("您没有权限执行此操作")
        
    conference = get_object_or_404(Conference, pk=pk)
    if request.method == 'POST':
        conference.delete()
        messages.success(request, '会议已删除！')
        return redirect('conference:list')
    
    return render(request, 'conferenceApp/conference_confirm_delete.html', {
        'conference': conference,
        'title': '删除会议'
    })

@login_required
def conference_register(request, pk):
    """会议报名视图"""
    conference = get_object_or_404(Conference, pk=pk)
    
    # 检查用户权限
    if request.user.is_admin:
        messages.error(request, '管理员不能报名参会')
        return redirect('conference:detail', pk=pk)
    
    # 检查会议状态和报名时间
    if conference.status != 'registration':
        messages.error(request, '当前不在报名时间内')
        return redirect('conference:detail', pk=pk)
    
    # 检查总人数限制
    current_participants = conference.registrations.filter(
        status__in=['pending', 'confirmed']
    ).count()
    if current_participants >= conference.max_participants:
        messages.error(request, '报名人数已达上限')
        return redirect('conference:detail', pk=pk)
    
    # 检查用户是否已报名
    if conference.registrations.filter(
        participant__user=request.user,
        status__in=['pending', 'confirmed']
    ).exists():
        messages.error(request, '您已经报名过此会议')
        return redirect('conference:detail', pk=pk)
    
    # 检查公司报名人数限制
    if hasattr(request.user, 'company') and request.user.company:
        company_participants = conference.registrations.filter(
            participant__user__company=request.user.company,
            status__in=['pending', 'confirmed']
        ).count()
        if company_participants >= conference.company_max_participants:
            messages.error(request, '您的公司报名人数已达上限')
            return redirect('conference:detail', pk=pk)
    
    # 创建报名记录
    try:
        with transaction.atomic():
            # 获取或创建参会人员记录
            participant, created = Participant.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.name,
                    'email': request.user.email,
                    'phone': request.user.phone
                }
            )
            
            # 获取或创建联系人记录
            contact_person, created = ContactPerson.objects.get_or_create(
                user=request.user,
                defaults={
                    'name': request.user.name,
                    'email': request.user.email,
                    'phone': request.user.phone
                }
            )
            
            # 创建报名记录
            registration = Registration.objects.create(
                conference=conference,
                participant=participant,
                contact_person=contact_person,
                form=conference.registration_form,
                status='pending',
                data={}  # 初始化空的表单数据
            )
            messages.success(request, '报名申请已提交，请等待审核')
    except Exception as e:
        messages.error(request, f'报名失败：{str(e)}')
        return redirect('conference:detail', pk=pk)
    
    return redirect('conference:detail', pk=pk)

from django.core.paginator import Paginator

@login_required
def manage_participants(request, conference_id):
    conference = get_object_or_404(Conference, id=conference_id)
    participants_list = Registration.objects.filter(conference=conference)

    # Handle search
    search_query = request.GET.get('search', '')
    if search_query:
        participants_list = participants_list.filter(
            Q(participant__name__icontains=search_query) |
            Q(participant__company__name__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(participants_list, 10)
    page_number = request.GET.get('page')
    participants = paginator.get_page(page_number)

    # Fetch tags and groups for batch operations
    tags = Tag.objects.all()
    groups = UserGroup.objects.all()

    context = {
        'conference': conference,
        'participants': participants,
        'tags': tags,
        'groups': groups,
    }
    return render(request, 'conferenceApp/participants.html', context)

@login_required
def create_participant(request, conference_id):
    conference = get_object_or_404(Conference, id=conference_id)
    if request.method == 'POST':
        # Handle form submission
        pass
    return render(request, 'conferenceApp/participant_form.html', {
        'conference': conference,
        'action': 'create'
    })

@login_required
def edit_participant(request, conference_id, participant_id):
    conference = get_object_or_404(Conference, id=conference_id)
    participant = get_object_or_404(Registration, id=participant_id, conference=conference)
    if request.method == 'POST':
        # Handle form submission
        pass
    return render(request, 'conferenceApp/participant_form.html', {
        'conference': conference,
        'participant': participant,
        'action': 'edit'
    })

@login_required
def conference_info(request, conference_id):
    """会务信息详情页"""
    conference = get_object_or_404(Conference, id=conference_id)
    
    # 通过 Registration 获取参会人
    registrations = Registration.objects.filter(conference=conference)
    
    # 获取当前用户的参会信息
    participant = None
    current_registration = None
    
    # 尝试找到当前用户的参会人员记录
    try:
        contact_person = ContactPerson.objects.get(user=request.user)
        current_registration = registrations.filter(contact_person=contact_person).first()
        
        if current_registration:
            participant = current_registration.participant
    except ContactPerson.DoesNotExist:
        pass
    
    # 默认会务信息
    default_schedule = [
        {
            "date": conference.start_date.strftime("%Y-%m-%d"),
            "sessions": [
                {"time": "08:00-09:00", "title": "签到", "location": "会议中心大厅"},
                {"time": "09:00-10:30", "title": "开幕式", "location": "主会场"},
                {"time": "10:30-12:00", "title": "主题报告", "location": "主会场"}
            ]
        }
    ]
    
    default_dinner_seating = {
        "venue": "会议中心宴会厅",
        "tables": [
            {"table_no": "A1", "seats": 10, "location": "一楼东侧"},
            {"table_no": "B2", "seats": 10, "location": "一楼西侧"}
        ]
    }
    
    # 使用默认值或已存储的值
    conference_schedule = conference.conference_schedule or default_schedule
    dinner_seating = conference.dinner_seating_info or default_dinner_seating
    
    # 获取当前激活的注意事项
    active_notice = Notice.objects.filter(is_active=True).first()
    
    context = {
        'conference': conference,
        'participant': participant,
        'registrations': registrations,
        'current_registration': current_registration,
        'conference_schedule': conference_schedule,
        'dinner_seating': dinner_seating,
        'active_notice': active_notice,
    }
    
    return render(request, 'conferenceApp/conference_info.html', context)

@login_required
def delete_contact(request, contact_id):
    """删除联系人"""
    contact = get_object_or_404(ContactPerson, id=contact_id)
    # 检查用户权限
    if request.user != contact.user and not request.user.is_staff:
        messages.error(request, "您没有权限删除此联系人")
        return redirect('conference:dashboard')
    
    # 记录日志
    logger.info(f"用户 {request.user.username} 删除了联系人 {contact.name}")
    
    # 删除联系人
    contact.delete()
    
    messages.success(request, f"联系人 {contact.name} 已成功删除")
    return redirect('conference:dashboard')
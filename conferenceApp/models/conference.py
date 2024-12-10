from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

class Conference(models.Model):
    """会议活动基本信息"""
    STATUS_CHOICES = (
        ('draft', '草稿'),
        ('published', '已发布'),
        ('registration', '报名中'),
        ('registration_ended', '报名结束'),
        ('check_in', '签到中'),
        ('in_progress', '进行中'),
        ('completed', '已结束'),
        ('cancelled', '已取消'),
    )

    name = models.CharField(max_length=200, verbose_name='会议名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='会议代码')
    description = models.TextField(verbose_name='会议描述')
    organizer = models.CharField(max_length=200, verbose_name='主办方')
    
    # 会议时间
    start_date = models.DateTimeField(verbose_name='会议开始时间')
    end_date = models.DateTimeField(verbose_name='会议结束时间')
    
    # 报名时间
    registration_start = models.DateTimeField(verbose_name='报名开始时间')
    registration_end = models.DateTimeField(verbose_name='报名截止时间')
    
    # 签到时间
    check_in_start = models.DateTimeField(verbose_name='签到开始时间')
    check_in_end = models.DateTimeField(verbose_name='签到结束时间')
    
    # 会议地点
    venue_name = models.CharField(max_length=200, verbose_name='会议地点名称')
    venue_address = models.TextField(verbose_name='会议地点详细地址')
    
    # 参会人数控制
    min_participants = models.IntegerField(default=1, verbose_name='最少参会人数')
    max_participants = models.IntegerField(verbose_name='最大参会人数')
    
    # 公司参会限制
    company_min_participants = models.IntegerField(default=1, verbose_name='每家公司最少参会人数')
    company_max_participants = models.IntegerField(verbose_name='每家公司最大参会人数')
    
    # 状态和设置
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='draft', verbose_name='会议状态')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    require_approval = models.BooleanField(default=False, verbose_name='是否需要审核')
    
    # 报名表单
    registration_form = models.ForeignKey(
        'RegistrationForm',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conferences',
        verbose_name='当前报名表单'
    )
    
    # 其他信息
    contact_person = models.CharField(max_length=100, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, verbose_name='联系电话')
    contact_email = models.EmailField(verbose_name='联系邮箱')
    
    # 附加信息
    additional_info = models.JSONField(default=dict, null=True, blank=True, verbose_name='附加信息')
    
    # 会务信息新增字段
    conference_notices = models.TextField(
        verbose_name='会议注意事项', 
        blank=True, 
        null=True, 
        help_text='包括行前准备、防疫要求等重要提示'
    )
    
    dinner_seating_info = models.JSONField(
        verbose_name='晚宴座位信息', 
        blank=True, 
        null=True, 
        help_text='存储晚宴座位安排的JSON数据'
    )
    
    conference_schedule = models.JSONField(
        verbose_name='会议日程', 
        blank=True, 
        null=True, 
        help_text='存储会议日程的详细安排'
    )
    
    emergency_contact = models.CharField(
        verbose_name='紧急联系人', 
        max_length=100, 
        blank=True, 
        null=True
    )
    
    emergency_phone = models.CharField(
        verbose_name='紧急联系电话', 
        max_length=20, 
        blank=True, 
        null=True
    )
    
    # 时间记录
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '会议活动'
        verbose_name_plural = '会议活动'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"

    def clean(self):
        # 验证时间的合法性
        if self.end_date <= self.start_date:
            raise ValidationError('会议结束时间必须晚于开始时间')
        
        if self.registration_end <= self.registration_start:
            raise ValidationError('报名结束时间必须晚于开始时间')
        
        if self.registration_end > self.start_date:
            raise ValidationError('报名必须在会议开始前结束')
        
        if self.check_in_end <= self.check_in_start:
            raise ValidationError('签到结束时间必须晚于签到开始时间')
        
        if self.check_in_start < self.registration_end:
            raise ValidationError('签到开始时间必须晚于报名结束时间')
        
        if self.check_in_end > self.start_date:
            raise ValidationError('签到必须在会议开始前结束')
        
        if self.company_max_participants < self.company_min_participants:
            raise ValidationError('每家公司最大参会人数必须大于最小参会人数')
        
        if self.max_participants < self.min_participants:
            raise ValidationError('最大参会人数必须大于最小参会人数')

    def update_status(self):
        """根据当前时间自动更新会议状态"""
        now = timezone.now()
        
        if self.status == 'cancelled':
            return
        
        if now < self.registration_start:
            if self.status == 'published':
                return
            self.status = 'published'
        elif self.registration_start <= now <= self.registration_end:
            self.status = 'registration'
        elif self.registration_end < now <= self.check_in_start:
            self.status = 'registration_ended'
        elif self.check_in_start <= now <= self.check_in_end:
            self.status = 'check_in'
        elif self.check_in_end < now <= self.start_date:
            self.status = 'registration_ended'
        elif self.start_date <= now <= self.end_date:
            self.status = 'in_progress'
        elif now > self.end_date:
            self.status = 'completed'
        
        self.save()

    def get_current_participants_count(self):
        """获取当前报名人数"""
        return self.registrations.filter(
            participant__status__in=['confirmed', 'checked_in']
        ).count()

    def can_register(self):
        """检查是否可以报名"""
        if self.status != 'registration':
            return False
        
        current_count = self.get_current_participants_count()
        return current_count < self.max_participants

    def get_company_participants_count(self, company):
        """获取指定公司的报名人数"""
        return self.registrations.filter(
            participant__company=company,
            participant__status__in=['confirmed', 'checked_in']
        ).count()

    def can_company_register(self, company):
        """检查指定公司是否可以继续报名"""
        current_count = self.get_company_participants_count(company)
        return current_count < self.company_max_participants

    def can_check_in(self):
        """检查是否可以签到"""
        if self.status != 'check_in':
            return False
        return True

    def get_checked_in_count(self):
        """获取已签到人数"""
        return self.registrations.filter(
            participant__status='checked_in'
        ).count()

    def get_check_in_rate(self):
        """获取签到率"""
        total = self.get_current_participants_count()
        if total == 0:
            return 0
        checked_in = self.get_checked_in_count()
        return (checked_in / total) * 100

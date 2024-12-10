from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from .conference import Conference

User = get_user_model()

class Survey(models.Model):
    """问卷调查模型"""
    STATUS_CHOICES = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('closed', '已关闭'),
    ]

    title = models.CharField('问卷标题', max_length=200)
    description = models.TextField('问卷说明', blank=True)
    formio_schema = models.JSONField('Form.io Schema')
    
    # 问卷状态
    status = models.CharField('状态', max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # 时间设置
    start_time = models.DateTimeField('开始时间', null=True, blank=True)
    end_time = models.DateTimeField('结束时间', null=True, blank=True)
    
    # 关联会议（可以关联多个会议）
    conferences = models.ManyToManyField(
        Conference,
        through='SurveyConference',
        related_name='surveys',
        verbose_name='关联会议'
    )
    
    # 创建和更新时间
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    # 创建者
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_surveys',
        verbose_name='创建者'
    )

    class Meta:
        verbose_name = '问卷调查'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def is_active(self):
        """检查问卷是否在活动时间内"""
        now = timezone.now()
        if self.status != 'published':
            return False
        if self.start_time and self.start_time > now:
            return False
        if self.end_time and self.end_time < now:
            return False
        return True

    def can_submit(self, user):
        """检查用户是否可以提交问卷"""
        return self.is_active and any(
            conference.participants.filter(id=user.id).exists()
            for conference in self.conferences.all()
        )

class SurveyConference(models.Model):
    """问卷和会议的关联模型"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, verbose_name='问卷')
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, verbose_name='会议')
    is_required = models.BooleanField('是否必填', default=False)
    created_at = models.DateTimeField('创建时间', auto_now_add=True)

    class Meta:
        verbose_name = '问卷-会议关联'
        verbose_name_plural = verbose_name
        unique_together = ('survey', 'conference')

    def __str__(self):
        return f'{self.survey.title} - {self.conference.name}'

class SurveyResponse(models.Model):
    """问卷回答模型"""
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name='问卷'
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='survey_responses',
        verbose_name='填写者'
    )
    conference = models.ForeignKey(
        Conference,
        on_delete=models.CASCADE,
        related_name='survey_responses',
        verbose_name='关联会议'
    )
    response_data = models.JSONField('回答数据')
    submitted_at = models.DateTimeField('提交时间', auto_now_add=True)
    
    class Meta:
        verbose_name = '问卷回答'
        verbose_name_plural = verbose_name
        unique_together = ('survey', 'user', 'conference')
        ordering = ['-submitted_at']

    def __str__(self):
        return f'{self.user.username} - {self.survey.title}'

class SurveyReminder(models.Model):
    """问卷提醒设置"""
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE, related_name='reminders')
    name = models.CharField("提醒名称", max_length=100)
    description = models.TextField("提醒描述", blank=True)
    
    # 提醒时间设置
    start_date = models.DateField("开始日期")
    end_date = models.DateField("结束日期")
    frequency = models.CharField("提醒频率", max_length=20, choices=[
        ('once', '单次'),
        ('daily', '每天'),
        ('weekly', '每周'),
        ('monthly', '每月')
    ])
    time = models.TimeField("提醒时间")
    
    # 提醒方式
    email_reminder = models.BooleanField("邮件提醒", default=True)
    sms_reminder = models.BooleanField("短信提醒", default=False)
    
    # 提醒对象
    ALL_PARTICIPANTS = 'all'
    INCOMPLETE_ONLY = 'incomplete'
    REMINDER_TARGET_CHOICES = [
        (ALL_PARTICIPANTS, '所有参与者'),
        (INCOMPLETE_ONLY, '未完成者'),
    ]
    target_participants = models.CharField(
        "提醒对象",
        max_length=20,
        choices=REMINDER_TARGET_CHOICES,
        default=ALL_PARTICIPANTS
    )
    
    # 提醒内容模板
    email_subject_template = models.CharField("邮件主题模板", max_length=200)
    email_body_template = models.TextField("邮件内容模板")
    sms_template = models.CharField("短信内容模板", max_length=500)
    
    # 状态跟踪
    is_active = models.BooleanField("是否启用", default=True)
    last_sent = models.DateTimeField("上次发送时间", null=True, blank=True)
    created_at = models.DateTimeField("创建时间", auto_now_add=True)
    updated_at = models.DateTimeField("更新时间", auto_now=True)
    
    class Meta:
        verbose_name = "问卷提醒"
        verbose_name_plural = "问卷提醒"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.survey.title} - {self.name}"

class ReminderLog(models.Model):
    """提醒发送日志"""
    reminder = models.ForeignKey(SurveyReminder, on_delete=models.CASCADE, related_name='logs')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE)
    sent_at = models.DateTimeField("发送时间", auto_now_add=True)
    type = models.CharField("提醒类型", max_length=10, choices=[('email', '邮件'), ('sms', '短信')])
    status = models.CharField("发送状态", max_length=20, choices=[
        ('success', '成功'),
        ('failed', '失败')
    ])
    error_message = models.TextField("错误信息", blank=True)
    
    class Meta:
        verbose_name = "提醒日志"
        verbose_name_plural = "提醒日志"
        ordering = ['-sent_at']

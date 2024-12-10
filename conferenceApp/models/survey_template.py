from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class SurveyTemplate(models.Model):
    """问卷模板模型"""
    CATEGORY_CHOICES = [
        ('satisfaction', '满意度调查'),
        ('feedback', '反馈收集'),
        ('registration', '报名登记'),
        ('evaluation', '会议评估'),
        ('other', '其他'),
    ]

    title = models.CharField('模板标题', max_length=200)
    description = models.TextField('模板说明', blank=True)
    category = models.CharField('模板类别', max_length=20, choices=CATEGORY_CHOICES, default='other')
    formio_schema = models.JSONField('Form.io Schema')
    is_public = models.BooleanField('是否公开', default=False)
    
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_templates',
        verbose_name='创建者'
    )
    created_at = models.DateTimeField('创建时间', auto_now_add=True)
    updated_at = models.DateTimeField('更新时间', auto_now=True)
    
    class Meta:
        verbose_name = '问卷模板'
        verbose_name_plural = verbose_name
        ordering = ['-created_at']
        
    def __str__(self):
        return f'{self.get_category_display()} - {self.title}'

from django.db import models
from .conference import Conference

class Contact(models.Model):
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE, related_name='contacts')
    name = models.CharField(max_length=100, verbose_name='姓名')
    title = models.CharField(max_length=100, verbose_name='职位', blank=True)
    phone = models.CharField(max_length=20, verbose_name='电话')
    email = models.EmailField(verbose_name='邮箱')
    description = models.TextField(verbose_name='描述', blank=True, help_text='联系人的其他信息，如负责的具体事项等')
    is_primary = models.BooleanField(default=False, verbose_name='主要联系人')
    
    class Meta:
        verbose_name = '联系人'
        verbose_name_plural = '联系人列表'
        ordering = ['-is_primary', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.title})"

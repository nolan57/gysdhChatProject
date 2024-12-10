from django.db import models
from django.conf import settings

class SupplierCompany(models.Model):
    name = models.CharField(max_length=200, verbose_name='公司名称')
    code = models.CharField(max_length=50, unique=True, verbose_name='公司编码')
    business_type = models.CharField(max_length=100, verbose_name='业务类型')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '供应商公司'
        verbose_name_plural = '供应商公司'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.code})"

class ContactPerson(models.Model):
    company = models.ForeignKey(SupplierCompany, on_delete=models.CASCADE, 
                              related_name='contacts', verbose_name='所属公司')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, 
                               related_name='contact_person', verbose_name='用户账号')
    position = models.CharField(max_length=100, verbose_name='职位')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    email = models.EmailField(verbose_name='邮箱')
    is_primary = models.BooleanField(default=False, verbose_name='是否为主要联系人')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '联系人'
        verbose_name_plural = '联系人'
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['company', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_contact'
            )
        ]

    def __str__(self):
        return f"{self.user.name} - {self.company.name}"

    def save(self, *args, **kwargs):
        # 如果设置为主要联系人，取消同一公司其他联系人的主要联系人状态
        if self.is_primary:
            ContactPerson.objects.filter(
                company=self.company,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)

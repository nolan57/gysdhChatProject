from django.db import models
from .company import SupplierCompany, ContactPerson

class Participant(models.Model):
    STATUS_CHOICES = (
        ('pending', '待确认'),
        ('confirmed', '已确认'),
        ('checked_in', '已签到'),
        ('cancelled', '已取消'),
    )

    company = models.ForeignKey(SupplierCompany, on_delete=models.CASCADE, 
                              related_name='participants', verbose_name='所属公司')
    registered_by = models.ForeignKey(ContactPerson, on_delete=models.CASCADE,
                                    related_name='registered_participants', verbose_name='登记人')
    name = models.CharField(max_length=100, verbose_name='姓名')
    position = models.CharField(max_length=100, verbose_name='职位')
    phone = models.CharField(max_length=20, verbose_name='联系电话')
    email = models.EmailField(verbose_name='邮箱')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, 
                            default='pending', verbose_name='状态')
    registration_number = models.CharField(max_length=50, unique=True, 
                                        verbose_name='登记编号')
    check_in_time = models.DateTimeField(null=True, blank=True, 
                                       verbose_name='签到时间')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')

    class Meta:
        verbose_name = '参会人员'
        verbose_name_plural = '参会人员'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['registration_number']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.name} - {self.company.name}"

    def save(self, *args, **kwargs):
        # 如果是新创建的参会人员，生成登记编号
        if not self.registration_number:
            self.registration_number = self._generate_registration_number()
        super().save(*args, **kwargs)

    def _generate_registration_number(self):
        """生成登记编号：公司编码 + 年月日 + 4位序号"""
        from django.utils import timezone
        import random
        import string

        date_str = timezone.now().strftime('%Y%m%d')
        company_code = self.company.code
        
        # 生成4位随机字符（数字和大写字母）
        random_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
        
        return f"{company_code}-{date_str}-{random_chars}"

    def check_in(self):
        """签到"""
        from django.utils import timezone
        if self.status == 'confirmed':
            self.status = 'checked_in'
            self.check_in_time = timezone.now()
            self.save()
            return True
        return False

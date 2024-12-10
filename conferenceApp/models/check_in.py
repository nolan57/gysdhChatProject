from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from .conference import Conference
from .venue import VenueRoom

class CheckInStation(models.Model):
    """签到站点"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='check_in_stations',
                                 verbose_name='会议')
    name = models.CharField(max_length=100, verbose_name='站点名称')
    location = models.CharField(max_length=200, verbose_name='位置')
    room = models.ForeignKey(VenueRoom, on_delete=models.SET_NULL,
                           related_name='check_in_stations',
                           null=True, blank=True,
                           verbose_name='所在房间')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '签到站点'
        verbose_name_plural = '签到站点'
        unique_together = ['conference', 'name']

    def __str__(self):
        return f"{self.conference.name} - {self.name}"

class CheckInRecord(models.Model):
    """签到记录"""
    CHECK_IN_TYPES = (
        ('regular', '常规签到'),
        ('late', '迟到签到'),
        ('manual', '人工签到'),
    )

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='check_in_records',
                                 verbose_name='会议')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE,
                                  related_name='check_in_records',
                                  verbose_name='参会者')
    station = models.ForeignKey(CheckInStation, on_delete=models.CASCADE,
                              related_name='check_in_records',
                              verbose_name='签到站点')
    check_in_type = models.CharField(max_length=20, choices=CHECK_IN_TYPES,
                                   default='regular', verbose_name='签到类型')
    check_in_time = models.DateTimeField(auto_now_add=True,
                                       verbose_name='签到时间')
    checked_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
                                 null=True, blank=True,
                                 related_name='handled_check_ins',
                                 verbose_name='签到处理人')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '签到记录'
        verbose_name_plural = '签到记录'
        unique_together = ['conference', 'participant']
        ordering = ['-check_in_time']

    def clean(self):
        # 检查会议是否在签到时间内
        from django.utils import timezone
        now = timezone.now()
        
        if now < self.conference.check_in_start:
            raise ValidationError('签到未开始')
        
        if now > self.conference.check_in_end:
            if self.check_in_type != 'manual':
                raise ValidationError('签到已结束')

        # 检查签到站点是否属于该会议
        if self.station.conference != self.conference:
            raise ValidationError('签到站点不属于该会议')

        # 检查签到站点是否启用
        if not self.station.is_active:
            raise ValidationError('该签到站点未启用')

    def save(self, *args, **kwargs):
        # 自动判断签到类型
        if not self.pk:  # 只在创建时判断
            from django.utils import timezone
            now = timezone.now()
            
            if self.checked_by:
                self.check_in_type = 'manual'
            elif now > self.conference.start_date:
                self.check_in_type = 'late'
            
            # 更新参会者状态
            self.participant.status = 'checked_in'
            self.participant.save()
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.conference.name} - {self.participant.name} - {self.check_in_time}"

class MaterialCollection(models.Model):
    """物料领取记录"""
    MATERIAL_TYPES = (
        ('badge', '胸卡'),
        ('materials', '会议资料'),
        ('gift', '礼品'),
    )

    check_in_record = models.ForeignKey(CheckInRecord,
                                      on_delete=models.CASCADE,
                                      related_name='material_collections',
                                      verbose_name='签到记录')
    material_type = models.CharField(max_length=20, choices=MATERIAL_TYPES,
                                   verbose_name='物料类型')
    collected_at = models.DateTimeField(auto_now_add=True,
                                      verbose_name='领取时间')
    collected = models.BooleanField(default=True, verbose_name='是否已领取')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '物料领取'
        verbose_name_plural = '物料领取'
        unique_together = ['check_in_record', 'material_type']

    def __str__(self):
        return (f"{self.check_in_record.participant.name} - "
                f"{self.get_material_type_display()}")

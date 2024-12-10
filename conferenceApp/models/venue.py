from django.db import models
from django.core.exceptions import ValidationError
from .conference import Conference

class Venue(models.Model):
    """会场信息"""
    name = models.CharField(max_length=200, verbose_name='会场名称')
    address = models.TextField(verbose_name='详细地址')
    description = models.TextField(null=True, blank=True, verbose_name='会场描述')
    capacity = models.IntegerField(verbose_name='容纳人数')
    floor_plan_image = models.ImageField(upload_to='venue/floor_plans/', 
                                       null=True, blank=True, 
                                       verbose_name='平面图')
    
    class Meta:
        verbose_name = '会场'
        verbose_name_plural = '会场'

    def __str__(self):
        return self.name

class VenueRoom(models.Model):
    """会议室/分会场"""
    ROOM_TYPES = (
        ('main', '主会场'),
        ('sub', '分会场'),
        ('meeting', '会议室'),
        ('rest', '休息室'),
    )

    venue = models.ForeignKey(Venue, on_delete=models.CASCADE, 
                            related_name='rooms', verbose_name='所属会场')
    name = models.CharField(max_length=100, verbose_name='房间名称')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES, 
                               verbose_name='房间类型')
    capacity = models.IntegerField(verbose_name='容纳人数')
    floor = models.CharField(max_length=50, verbose_name='所在楼层')
    room_number = models.CharField(max_length=50, verbose_name='房间号')
    
    class Meta:
        verbose_name = '会议室'
        verbose_name_plural = '会议室'
        unique_together = ['venue', 'room_number']

    def __str__(self):
        return f"{self.venue.name} - {self.name}"

class Seat(models.Model):
    """座位信息"""
    SEAT_TYPES = (
        ('regular', '普通座位'),
        ('vip', 'VIP座位'),
        ('speaker', '演讲者座位'),
        ('staff', '工作人员座位'),
    )

    room = models.ForeignKey(VenueRoom, on_delete=models.CASCADE, 
                           related_name='seats', verbose_name='所属房间')
    seat_number = models.CharField(max_length=20, verbose_name='座位号')
    seat_type = models.CharField(max_length=20, choices=SEAT_TYPES, 
                               default='regular', verbose_name='座位类型')
    row = models.CharField(max_length=10, verbose_name='排号')
    column = models.CharField(max_length=10, verbose_name='列号')
    is_available = models.BooleanField(default=True, verbose_name='是否可用')
    notes = models.CharField(max_length=200, null=True, blank=True, 
                           verbose_name='备注')

    class Meta:
        verbose_name = '座位'
        verbose_name_plural = '座位'
        unique_together = ['room', 'seat_number']
        ordering = ['row', 'column']

    def __str__(self):
        return f"{self.room.name} - {self.seat_number}"

class SeatAssignment(models.Model):
    """座位分配"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='seat_assignments',
                                 verbose_name='会议')
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE,
                           related_name='assignments', verbose_name='座位')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE,
                                  related_name='seat_assignments',
                                  verbose_name='参会者')
    assigned_at = models.DateTimeField(auto_now_add=True, verbose_name='分配时间')
    notes = models.CharField(max_length=200, null=True, blank=True,
                           verbose_name='备注')

    class Meta:
        verbose_name = '座位分配'
        verbose_name_plural = '座位分配'
        unique_together = [
            ['conference', 'seat'],
            ['conference', 'participant']
        ]

    def clean(self):
        if not self.seat.is_available:
            raise ValidationError('该座位不可用')
        
        if self.seat.seat_type == 'vip' and not self.participant.is_vip:
            raise ValidationError('该座位仅供VIP使用')

    def __str__(self):
        return f"{self.conference.name} - {self.participant.name} - {self.seat.seat_number}"

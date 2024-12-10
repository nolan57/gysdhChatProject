from django.db import models
from django.core.exceptions import ValidationError
from .conference import Conference

class Hotel(models.Model):
    """酒店信息"""
    name = models.CharField(max_length=200, verbose_name='酒店名称')
    address = models.TextField(verbose_name='详细地址')
    description = models.TextField(null=True, blank=True, verbose_name='酒店描述')
    contact_person = models.CharField(max_length=100, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, verbose_name='联系电话')
    star_rating = models.IntegerField(verbose_name='星级')
    
    class Meta:
        verbose_name = '酒店'
        verbose_name_plural = '酒店'

    def __str__(self):
        return self.name

class RoomType(models.Model):
    """房间类型"""
    ROOM_TYPES = (
        ('single', '单人间'),
        ('double', '双人间'),
        ('suite', '套房'),
        ('deluxe', '豪华间'),
    )

    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE,
                            related_name='room_types', verbose_name='所属酒店')
    name = models.CharField(max_length=100, verbose_name='房型名称')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPES,
                               verbose_name='房间类型')
    price = models.DecimalField(max_digits=10, decimal_places=2,
                              verbose_name='房价')
    capacity = models.IntegerField(verbose_name='可住人数')
    description = models.TextField(null=True, blank=True, verbose_name='房型描述')
    
    class Meta:
        verbose_name = '房间类型'
        verbose_name_plural = '房间类型'

    def __str__(self):
        return f"{self.hotel.name} - {self.name}"

class Room(models.Model):
    """具体房间"""
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE,
                                related_name='rooms', verbose_name='房型')
    room_number = models.CharField(max_length=20, verbose_name='房间号')
    floor = models.CharField(max_length=10, verbose_name='楼层')
    status = models.CharField(max_length=20, 
                            choices=[
                                ('available', '可用'),
                                ('occupied', '已占用'),
                                ('maintenance', '维护中'),
                            ],
                            default='available',
                            verbose_name='状态')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '房间'
        verbose_name_plural = '房间'
        unique_together = ['room_type', 'room_number']

    def __str__(self):
        return f"{self.room_type.hotel.name} - {self.room_number}"

class Accommodation(models.Model):
    """住宿安排"""
    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='accommodations',
                                 verbose_name='会议')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE,
                                  related_name='accommodations',
                                  verbose_name='参会者')
    room = models.ForeignKey(Room, on_delete=models.CASCADE,
                           related_name='accommodations',
                           verbose_name='房间')
    check_in_date = models.DateField(verbose_name='入住日期')
    check_out_date = models.DateField(verbose_name='退房日期')
    status = models.CharField(max_length=20,
                            choices=[
                                ('pending', '待确认'),
                                ('confirmed', '已确认'),
                                ('checked_in', '已入住'),
                                ('checked_out', '已退房'),
                                ('cancelled', '已取消'),
                            ],
                            default='pending',
                            verbose_name='状态')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '住宿安排'
        verbose_name_plural = '住宿安排'

    def clean(self):
        if self.check_out_date <= self.check_in_date:
            raise ValidationError('退房日期必须晚于入住日期')
        
        # 检查日期是否在会议期间
        if (self.check_in_date > self.conference.end_date.date() or
            self.check_out_date < self.conference.start_date.date()):
            raise ValidationError('住宿日期必须在会议期间内')

        # 检查房间容量
        current_occupants = Accommodation.objects.filter(
            room=self.room,
            status__in=['confirmed', 'checked_in'],
            check_in_date__lte=self.check_out_date,
            check_out_date__gte=self.check_in_date
        ).exclude(id=self.id).count()

        if current_occupants >= self.room.room_type.capacity:
            raise ValidationError('该房间在指定日期已满')

    def __str__(self):
        return (f"{self.conference.name} - {self.participant.name} - "
                f"{self.room.room_number}")

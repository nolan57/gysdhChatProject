from django.db import models
from django.core.exceptions import ValidationError
from .conference import Conference

class Vehicle(models.Model):
    """车辆信息"""
    VEHICLE_TYPES = (
        ('bus', '大巴'),
        ('van', '面包车'),
        ('car', '轿车'),
    )

    vehicle_type = models.CharField(max_length=20, choices=VEHICLE_TYPES,
                                  verbose_name='车辆类型')
    plate_number = models.CharField(max_length=20, unique=True,
                                  verbose_name='车牌号')
    capacity = models.IntegerField(verbose_name='载客量')
    driver_name = models.CharField(max_length=100, verbose_name='司机姓名')
    driver_phone = models.CharField(max_length=20, verbose_name='司机电话')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '车辆'
        verbose_name_plural = '车辆'

    def __str__(self):
        return f"{self.get_vehicle_type_display()} - {self.plate_number}"

class Route(models.Model):
    """路线信息"""
    ROUTE_TYPES = (
        ('airport_pickup', '机场接机'),
        ('airport_dropoff', '机场送机'),
        ('hotel_venue', '酒店-会场'),
        ('custom', '自定义路线'),
    )

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='routes', verbose_name='会议')
    name = models.CharField(max_length=200, verbose_name='路线名称')
    route_type = models.CharField(max_length=20, choices=ROUTE_TYPES,
                                verbose_name='路线类型')
    start_location = models.CharField(max_length=200, verbose_name='起点')
    end_location = models.CharField(max_length=200, verbose_name='终点')
    estimated_duration = models.DurationField(verbose_name='预计用时')
    description = models.TextField(null=True, blank=True, verbose_name='路线描述')

    class Meta:
        verbose_name = '路线'
        verbose_name_plural = '路线'

    def __str__(self):
        return f"{self.conference.name} - {self.name}"

class Trip(models.Model):
    """行程安排"""
    route = models.ForeignKey(Route, on_delete=models.CASCADE,
                            related_name='trips', verbose_name='路线')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE,
                              related_name='trips', verbose_name='车辆')
    departure_time = models.DateTimeField(verbose_name='出发时间')
    arrival_time = models.DateTimeField(verbose_name='到达时间')
    max_passengers = models.IntegerField(verbose_name='最大乘客数')
    status = models.CharField(max_length=20,
                            choices=[
                                ('scheduled', '已安排'),
                                ('in_progress', '进行中'),
                                ('completed', '已完成'),
                                ('cancelled', '已取消'),
                            ],
                            default='scheduled',
                            verbose_name='状态')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '行程'
        verbose_name_plural = '行程'

    def clean(self):
        if self.arrival_time <= self.departure_time:
            raise ValidationError('到达时间必须晚于出发时间')
        
        if self.max_passengers > self.vehicle.capacity:
            raise ValidationError('最大乘客数不能超过车辆载客量')

    def __str__(self):
        return f"{self.route.name} - {self.departure_time}"

class TripRegistration(models.Model):
    """行程登记"""
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE,
                           related_name='registrations', verbose_name='行程')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE,
                                  related_name='trip_registrations',
                                  verbose_name='参会者')
    status = models.CharField(max_length=20,
                            choices=[
                                ('registered', '已登记'),
                                ('confirmed', '已确认'),
                                ('boarded', '已上车'),
                                ('completed', '已完成'),
                                ('cancelled', '已取消'),
                            ],
                            default='registered',
                            verbose_name='状态')
    luggage_count = models.IntegerField(default=0, verbose_name='行李数量')
    special_requirements = models.TextField(null=True, blank=True,
                                         verbose_name='特殊要求')
    registration_time = models.DateTimeField(auto_now_add=True,
                                           verbose_name='登记时间')
    boarding_time = models.DateTimeField(null=True, blank=True,
                                       verbose_name='上车时间')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '行程登记'
        verbose_name_plural = '行程登记'
        unique_together = ['trip', 'participant']

    def clean(self):
        # 检查行程容量
        current_registrations = TripRegistration.objects.filter(
            trip=self.trip,
            status__in=['registered', 'confirmed', 'boarded']
        ).exclude(id=self.id).count()

        if current_registrations >= self.trip.max_passengers:
            raise ValidationError('该行程已达到最大乘客数')

    def __str__(self):
        return f"{self.trip} - {self.participant.name}"

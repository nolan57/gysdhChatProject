from django.db import models
from django.core.exceptions import ValidationError
from .conference import Conference

class Restaurant(models.Model):
    """餐厅信息"""
    name = models.CharField(max_length=200, verbose_name='餐厅名称')
    location = models.CharField(max_length=200, verbose_name='位置')
    capacity = models.IntegerField(verbose_name='容纳人数')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    contact_person = models.CharField(max_length=100, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, verbose_name='联系电话')

    class Meta:
        verbose_name = '餐厅'
        verbose_name_plural = '餐厅'

    def __str__(self):
        return self.name

class Meal(models.Model):
    """餐次设置"""
    MEAL_TYPES = (
        ('breakfast', '早餐'),
        ('lunch', '午餐'),
        ('dinner', '晚餐'),
        ('tea_break', '茶歇'),
    )

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE,
                                 related_name='meals', verbose_name='会议')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE,
                                 related_name='meals', verbose_name='餐厅')
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES,
                               verbose_name='餐次类型')
    date = models.DateField(verbose_name='日期')
    start_time = models.TimeField(verbose_name='开始时间')
    end_time = models.TimeField(verbose_name='结束时间')
    max_capacity = models.IntegerField(verbose_name='最大接待人数')
    
    class Meta:
        verbose_name = '餐次'
        verbose_name_plural = '餐次'
        unique_together = ['conference', 'restaurant', 'meal_type', 'date']

    def __str__(self):
        return f"{self.conference.name} - {self.get_meal_type_display()} - {self.date}"

    def clean(self):
        if self.end_time <= self.start_time:
            raise ValidationError('结束时间必须晚于开始时间')
        
        if self.max_capacity > self.restaurant.capacity:
            raise ValidationError('最大接待人数不能超过餐厅容量')

class MealOption(models.Model):
    """餐饮选项"""
    DIET_TYPES = (
        ('regular', '普通'),
        ('vegetarian', '素食'),
        ('halal', '清真'),
        ('diabetes', '糖尿病餐'),
    )

    meal = models.ForeignKey(Meal, on_delete=models.CASCADE,
                           related_name='options', verbose_name='餐次')
    name = models.CharField(max_length=100, verbose_name='选项名称')
    diet_type = models.CharField(max_length=20, choices=DIET_TYPES,
                               default='regular', verbose_name='饮食类型')
    description = models.TextField(null=True, blank=True, verbose_name='描述')
    max_quantity = models.IntegerField(verbose_name='最大供应数量')
    
    class Meta:
        verbose_name = '餐饮选项'
        verbose_name_plural = '餐饮选项'

    def __str__(self):
        return f"{self.meal} - {self.name}"

class MealRegistration(models.Model):
    """用餐登记"""
    meal = models.ForeignKey(Meal, on_delete=models.CASCADE,
                           related_name='registrations', verbose_name='餐次')
    participant = models.ForeignKey('Participant', on_delete=models.CASCADE,
                                  related_name='meal_registrations',
                                  verbose_name='参会者')
    meal_option = models.ForeignKey(MealOption, on_delete=models.CASCADE,
                                  related_name='registrations',
                                  verbose_name='餐饮选项')
    status = models.CharField(max_length=20,
                            choices=[
                                ('registered', '已登记'),
                                ('attended', '已用餐'),
                                ('cancelled', '已取消'),
                            ],
                            default='registered',
                            verbose_name='状态')
    registration_time = models.DateTimeField(auto_now_add=True,
                                           verbose_name='登记时间')
    attendance_time = models.DateTimeField(null=True, blank=True,
                                         verbose_name='用餐时间')
    notes = models.TextField(null=True, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '用餐登记'
        verbose_name_plural = '用餐登记'
        unique_together = ['meal', 'participant']

    def clean(self):
        # 检查餐次容量
        current_registrations = MealRegistration.objects.filter(
            meal=self.meal,
            status__in=['registered', 'attended']
        ).exclude(id=self.id).count()

        if current_registrations >= self.meal.max_capacity:
            raise ValidationError('该餐次已达到最大容量')

        # 检查餐饮选项数量
        option_registrations = MealRegistration.objects.filter(
            meal_option=self.meal_option,
            status__in=['registered', 'attended']
        ).exclude(id=self.id).count()

        if option_registrations >= self.meal_option.max_quantity:
            raise ValidationError('该餐饮选项已达到最大供应数量')

    def __str__(self):
        return f"{self.meal} - {self.participant.name}"

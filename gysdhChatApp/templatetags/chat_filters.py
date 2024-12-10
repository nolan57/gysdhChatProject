from django import template
from django.utils import timezone

register = template.Library()

@register.filter
def timesince_minutes(value):
    """
    返回从给定时间到现在的分钟数
    """
    if not value:
        return 0
    
    now = timezone.now()
    diff = now - value
    
    return diff.total_seconds() / 60

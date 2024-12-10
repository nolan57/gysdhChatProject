from django import template
from django.forms.widgets import Input, Textarea, Select, CheckboxInput

register = template.Library()

@register.filter(name='addclass')
def addclass(field, css_classes):
    """
    添加CSS类到表单字段
    用法: {{ field|addclass:"class1 class2" }}
    """
    if isinstance(field.field.widget, (Input, Textarea, Select)):
        return field.as_widget(attrs={"class": css_classes})
    elif isinstance(field.field.widget, CheckboxInput):
        return field.as_widget(attrs={"class": f"{css_classes} h-4 w-4"})
    return field

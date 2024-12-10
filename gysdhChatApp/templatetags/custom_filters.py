from django import template

register = template.Library()

@register.filter
def modulo(value, arg):
    """返回value除以arg的余数"""
    return int(value) % int(arg)

@register.filter
def user_color(value):
    """根据用户ID返回一个颜色类名"""
    colors = ['blue', 'green', 'yellow', 'red', 'indigo', 'pink']
    return colors[int(value) % len(colors)]

@register.filter
def is_image(file_name):
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
    if not file_name:
        return False
    file_name = str(file_name).lower()
    return any(file_name.endswith(ext) for ext in image_extensions)

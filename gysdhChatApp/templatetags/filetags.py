from django import template

register = template.Library()

@register.filter
def is_image(value):
    """Check if file name ends with common image extensions."""
    if hasattr(value, 'name'):
        filename = value.name
    else:
        filename = str(value)
    return filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))

@register.filter
def endswith(value, suffix):
    """Check if string ends with the given suffix."""
    if hasattr(value, 'name'):
        value = value.name
    return str(value).lower().endswith(suffix.lower())
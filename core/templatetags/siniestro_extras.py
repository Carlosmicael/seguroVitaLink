# En tu app/templatetags/siniestro_extras.py
from django import template

register = template.Library()

@register.filter(name='abs')
def abs_filter(value):
    try:
        return abs(int(value))
    except (ValueError, TypeError):
        return value
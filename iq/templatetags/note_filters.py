from django import template

register = template.Library()

@register.filter
def divide(value, arg):
    """Divide the value by arg and return rounded integer"""
    try:
        value = int(value)
        arg = int(arg)
        if arg == 0:
            return 0
        return round(value / arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter
def multiply(value, arg):
    """Multiply value by arg"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Subtract arg from value"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0
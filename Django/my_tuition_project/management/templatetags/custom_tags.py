from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter
def multiply(value, arg):
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def divide(value, arg):
    try:
        return float(value) / float(arg) if float(arg) != 0 else 0
    except (ValueError, TypeError):
        return 0
    

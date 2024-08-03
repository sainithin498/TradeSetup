from django import template
register = template.Library()

@register.filter
def timeformat(value):
    """Removes all values of arg from the given string"""
    return value.astimezone().strftime("%d-%m-%Y %H:%M:%S")
from django import template

register = template.Library()

@register.filter(name="split")
def split(value, key):
    return value.split(key)

@register.filter
def replace(value,key):
    return value.replace(key," ").title()




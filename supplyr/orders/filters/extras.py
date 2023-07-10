from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def do_something(html_code, invoice):
    code = template.Template(html_code)
    context = template.Context({'invoice':invoice})
    return code.render(context)

@register.filter
def apply_seller_currency(amount,invoice):
    currency_representation = invoice.order.seller.currency_representation if invoice.order.seller.currency_representation else '${{amount}}'
    code = template.Template(f'<span>{currency_representation}</span>')
    context = template.Context({'amount':amount,'amount_no_decimals':int(amount)})
    return code.render(context)

@register.filter
def get_status_variable_value(order,slug):
    print(" Order Status Variable value ",order,slug)
    value = ""
    try:
        value = order.status_variable_values.get(variable__slug=slug).value
    except:
        value = ""
    return value
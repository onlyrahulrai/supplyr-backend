from django import template
from django.utils.safestring import mark_safe
from functools import reduce

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
    
@register.filter
def get_ordergroup_total(items):
    return reduce(lambda prev,curr: {
        "subtotal": prev["subtotal"] + curr["subtotal"],
        "extra_discount": prev["extra_discount"] + (curr["extra_discount"] * curr["quantity"]),
        "igst": prev["igst"] + curr["igst"],
        "cgst": prev["cgst"] + curr["cgst"],
        "sgst": prev["sgst"] + curr["sgst"],
        "taxable_amount": prev["taxable_amount"] + curr["taxable_amount"],
        'total_amount': prev['total_amount'] + curr['total_amount']
    },
    items,
    {
    "subtotal": 0,
    "extra_discount": 0,
    "igst": 0,
    "cgst": 0,
    "sgst": 0,
    "taxable_amount": 0,
    'total_amount': 0
})
    
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

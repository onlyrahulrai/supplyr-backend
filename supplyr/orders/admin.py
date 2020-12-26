# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Order, OrderItem, OrderHistory


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'buyer',
        'seller',
        'created_at',
        'is_active',
        'cancelled_at',
        'cancelled_by',
        'total_amount',
    )
    list_filter = (
        'buyer',
        'seller',
        'created_at',
        'is_active',
        'cancelled_at',
    )
    date_hierarchy = 'created_at'


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order',
        'product_variant',
        'quantity',
        'price',
        'sale_price',
    )
    list_filter = ('order', 'product_variant')

admin.site.register(OrderHistory)
# -*- coding: utf-8 -*-
from django.contrib import admin

from .models import Invoice, Order, OrderItem, OrderHistory, OrderStatusVariable, OrderStatusVariableValue


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
        'actual_price',
    )
    list_filter = ('order', 'product_variant')

admin.site.register(OrderHistory)


@admin.register(OrderStatusVariable)
class OrderStatusVariableAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'description', 'is_active')
    list_filter = ('is_active',)
    # raw_id_fields = ('sellers',)
    search_fields = ('name',)


@admin.register(OrderStatusVariableValue)
class OrderStatusVariableValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'variable', 'value')
    list_filter = ('order', 'variable')
    
admin.site.register(Invoice)
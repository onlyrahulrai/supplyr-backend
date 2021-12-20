# -*- coding: utf-8 -*-
from django.contrib import admin


from .models import Invoice, Order, OrderItem, OrderHistory, OrderStatusChoices, OrderStatusVariable, OrderStatusVariableValue


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
    list_display = ('id', 'name', 'linked_order_status', 'data_type', 'is_active', 'slug')
    list_filter = ('is_active',)
    # raw_id_fields = ('sellers',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ['name']}


@admin.register(OrderStatusVariableValue)
class OrderStatusVariableValueAdmin(admin.ModelAdmin):
    list_display = ('id', 'order', 'variable', 'value')
    list_filter = ('order', 'variable')


@admin.register(OrderStatusChoices)
class OrderStatusChoicesAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'slug', 'serial')
    search_fields = ('name', 'slug')
    prepopulated_fields = {'slug': ['name']}
    
    
admin.site.register(Invoice)

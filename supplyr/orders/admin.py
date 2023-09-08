# -*- coding: utf-8 -*-
from django.contrib import admin


from .models import *

admin.site.register(OrderGroup)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'order_number',
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
        'item_note',
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
    
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id","seller","buyer","amount","mode","remarks")
    
admin.site.register(Ledger)
    
admin.site.register(Invoice)

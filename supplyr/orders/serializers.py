from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction

from .models import *
from supplyr.inventory.models import Variant
from supplyr.profiles.models import BuyerAddress

class OrderItemSerializer(serializers.ModelSerializer):
    class Meta: 
        model = OrderItem
        exclude = ['id', 'order']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        exclude = ['is_active']
        read_only_fields = ['cancelled_at']

    def to_internal_value(self, data):
        print('xAMEEE', data)
        # internal_value = super().to_internal_value(data)
        print('xAMEEEa')
        unhandled_errors = False
        # handled_errors = False
        total_amount = 0
        seller_id = None
        buyer_profile = self.context['request'].user.get_buyer_profile()
        print(data['items'])
        for item in data['items']:
            error = None
            variant = Variant.objects.filter(id=item['variant_id'], is_active=True).first()
            if not variant:
                unhandled_errors =  True
            if variant.quantity < item['quantity']:
                raise ValidationError({"message": "Selcted quantities of some products no longer available."})
                # handled_errors = "Selcted quantities of some products no longer available."
            
            if unhandled_errors:
                raise serializers.ValidationError({"Data not validated.": ''})
            #Raise exxception

            item['price'] = variant.price
            item['sale_price'] = variant.sale_price
            item['product_variant'] = item['variant_id']
            total_amount += (item['sale_price'] or item['price'])
            if not seller_id:
                seller_id = variant.product.owner_id
            elif seller_id != variant.product.owner_id:
                handled_errors = "Incorrect Data ! Sellers of all items do not match"

        
        data['total_amount'] = total_amount
        data['seller'] = seller_id
            

        data['buyer'] = buyer_profile.id
        return super().to_internal_value(data)

    def create(self, validated_data): 
        # Validation TBA: Prevent any extra field in api call, like is_cancelled, created_at etc which should not be set by user api call 
        # validation TBA: check if buyer n seller are connected
        items = validated_data.pop('items')
        print("VDDDDD ", validated_data)
        # address = BuyerAddress.objectaddressed_data)
        if validated_data['address'].owner_id != validated_data['buyer'].id:
            raise ValidationError({"message": "Invalid Address"})

        with transaction.atomic():
            order = Order.objects.create(**validated_data, buyer_id=6)
            for item in items:
                OrderItem.objects.create(**item, order = order)
        
        return order
            

class OrderListSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    def get_featured_image(self, order):
        if im := order.featured_image:
            return order.featured_image.image_md.url

    order_date = serializers.SerializerMethodField()
    def get_order_date(self, order):
        return order.created_at.strftime("%b %I, %Y")

    seller_name = serializers.SerializerMethodField()
    def get_seller_name(self, order):
        return order.seller.business_name
    
    items_count = serializers.SerializerMethodField()
    def get_items_count(self, order):
        return order.items.count()

    order_status = serializers.SerializerMethodField()
    def get_order_status(self, order):
        return order.status

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'seller_name', 'items_count', 'order_status', 'total_amount', 'featured_image',]
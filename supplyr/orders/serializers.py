from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone
from django.db.models import F
from datetime import timedelta

from .models import *
from supplyr.inventory.models import Variant
from supplyr.profiles.models import BuyerAddress
from supplyr.profiles.serializers import BuyerAddressSerializer
from supplyr.inventory.serializers import VariantDetailsSerializer

class OrderItemSerializer(serializers.ModelSerializer):
    # featured_image = serializers.SerializerMethodField()
    # def get_featured_image(self, order):
    #     if im := order.featured_image:
    #         return order.featured_image.image_md.url

    # title = serializers.CharField(source='product_variant.product.title')
    product_variant = VariantDetailsSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(queryset=Variant.objects.all(), source='product_variant', write_only=True)
    class Meta: 
        model = OrderItem
        fields = ['quantity', 'price', 'sale_price', 'product_variant', 'product_variant_id']

class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True)

    class Meta:
        model = Order
        exclude = ['is_active']
        read_only_fields = ['cancelled_at']

    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None

    def to_internal_value(self, data):
        unhandled_errors = False
        # handled_errors = False
        total_amount = 0
        seller_id = None
        if 'buyer_id' in data and self.context['request'].user.salesperson_status == 'ready':
            buyer_id = data.pop('buyer_id')
            buyer_profile_id =  buyer_id
        else:
            buyer_profile_id = self.context['request'].user.get_buyer_profile().id
        print(data['items'])
        for item in data['items']:
            error = None
            variant = Variant.objects.filter(id=item['variant_id'], is_active=True).first()
            if not variant:
                unhandled_errors =  True
            if variant.quantity < item['quantity']:
                raise ValidationError({"cart": "Selcted quantities of some products no longer available."})
                # handled_errors = "Selcted quantities of some products no longer available."
            
            if unhandled_errors:
                raise serializers.ValidationError({"Data not validated.": ''})
            #Raise exxception

            item['price'] = variant.price
            item['sale_price'] = variant.sale_price or variant.price
            item['product_variant_id'] = item['variant_id']
            total_amount += (item['sale_price'] or item['price'])*item['quantity']
            if not seller_id:
                seller_id = variant.product.owner_id
            elif seller_id != variant.product.owner_id:
                handled_errors = "Incorrect Data ! Sellers of all items do not match"

        
        data['total_amount'] = total_amount
        data['seller'] = seller_id
            

        data['buyer'] = buyer_profile_id
        return super().to_internal_value(data)

    def create(self, validated_data): 
        # Validation TBA: Prevent any extra field in api call, like is_cancelled, created_at etc which should not be set by user api call 
        # validation TBA: check if buyer n seller are connected
        items = validated_data.pop('items')
        print("VDDDDD ", validated_data)
        # address = BuyerAddress.objectaddressed_data)
        if self._get_api_source() != 'sales' and validated_data['address'].owner_id != validated_data['buyer'].id:
            raise ValidationError({"message": "Invalid Address"})
        if self._get_api_source() == 'sales':
            validated_data['salesperson'] = self.context['request'].user.get_sales_profile()


        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for item in items:
                _item = OrderItem.objects.create(**item, order = order)

                product_variant = _item.product_variant
                product_variant.quantity = F('quantity') - _item.quantity
                product_variant.save()
        
        return order
            

class OrderListSerializer(serializers.ModelSerializer):
    featured_image = serializers.SerializerMethodField()
    def get_featured_image(self, order):
        if im := order.featured_image:
            return order.featured_image.image_md.url

    order_date = serializers.SerializerMethodField()
    def get_order_date(self, order):
        tdelta = timezone.now() - order.created_at 
        if tdelta.days == 0:
            return naturaltime(order.created_at)

        elif tdelta.days == 1 and (timezone.now() - timedelta(days=1)).day == order.created_at.day:
            return 'yesterday'

        return order.created_at.strftime("%b %d, %Y")

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

class SellerOrderListSerializer(OrderListSerializer):

    buyer_name = serializers.SerializerMethodField()
    def get_buyer_name(self, order):
        return order.buyer.business_name

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'buyer_name', 'order_status', 'total_amount', 'featured_image',]

class SalespersonOrderListSerializer(OrderListSerializer):

    buyer_name = serializers.SerializerMethodField()
    def get_buyer_name(self, order):
        return order.buyer.business_name

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'buyer_name', 'order_status', 'total_amount', 'featured_image',]



class OrderDetailsSerializer(SellerOrderListSerializer):

    address = BuyerAddressSerializer()
    items = OrderItemSerializer(many=True)

    def get_order_date(self, order):
        return order.created_at.strftime("%b %d, %Y")

    class Meta:
        model = Order
        fields=['order_date', 'seller_name', 'buyer_name', 'order_status', 'total_amount', 'items', 'address']
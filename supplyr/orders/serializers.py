from supplyr.utils.api.mixins import SerializerAPISourceMixin
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.db import transaction
from django.contrib.humanize.templatetags.humanize import naturaltime
from django.utils import timezone
from django.db.models import F,Q
from datetime import timedelta

from .models import *
from supplyr.profiles.models import InvoiceTemplate,BuyerProfile,BuyerAddress
from supplyr.inventory.models import Variant
from supplyr.profiles.serializers import BuyerAddressSerializer
from supplyr.inventory.serializers import VariantDetailsSerializer
from supplyr.orders.models import Payment,Ledger
from django.shortcuts import get_object_or_404
from supplyr.core.functions import render_to_pdf
from io import BytesIO
from django.core.files import File
from supplyr.discounts.serializers import BuyerShortDetailSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    # featured_image = serializers.SerializerMethodField()
    # def get_featured_image(self, order):
    #     if im := order.featured_image:
    #         return order.featured_image.image_md.url
    
    product_variant = VariantDetailsSerializer(read_only=True)
    product_variant_id = serializers.PrimaryKeyRelatedField(queryset=Variant.objects.all(), source='product_variant', write_only=True)
    
    def to_representation(self, instance):
        output = super(OrderItemSerializer, self).to_representation(instance)
        output["cgst"] = float(instance.cgst)
        output["sgst"] = float(instance.sgst)
        output["igst"] = float(instance.igst)
        output["extra_discount"] = float(instance.extra_discount)
        output["taxable_amount"] = float(instance.taxable_amount)
        output['total_amount'] = float(instance.total_amount)
        output['subtotal'] = float(instance.subtotal)
        output["tax_amount"] = float(instance.tax_amount)
        output["price"] = float(instance.price)
        output["actual_price"] = float(instance.actual_price)
        output["subtotal"] = float(instance.subtotal)
        return output
    
    class Meta: 
        model = OrderItem
        fields = ["id", 'quantity', 'item_note','taxable_amount',"tax_amount",'subtotal','total_amount','cgst','sgst','igst','price', 'actual_price',"extra_discount" ,'product_variant', 'product_variant_id']

class OrderSerializer(serializers.ModelSerializer):
    
    # items = OrderItemSerializer(many=True)
    items = serializers.SerializerMethodField()
    def get_items(self,order):
        orderitem = order.items.filter(is_active=True)
        print(f"\n\n\n orderitem queryset >>>>> {orderitem} \n\n\n")
        return OrderItemSerializer(orderitem,many=True).data

    class Meta:
        model = Order
        fields = ["id","order_number","items","buyer","seller","created_by","subtotal","total_amount","total_extra_discount","taxable_amount","sgst","cgst","igst","address","status","created_at","cancelled_at","cancelled_by","is_paid"]
        # exclude = ['is_active']
        read_only_fields = ['order_number','cancelled_at']

    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None

    def to_internal_value(self, data):
        print(f"\n\n\n requested data is {data} \n\n\n")
        print("validated data >>>>>>>>>>>> ",data.get("discount"))
        unhandled_errors = False
        # handled_errors = False
        subtotal = 0
        seller_id = None
        
        if "buyer_id" in data and (self.context["request"].user.seller_status == "approved" or self.context['request'].user.salesperson_status == 'ready'):
            buyer_id = data.pop("buyer_id")
            buyer_profile_id = buyer_id
        else:
            buyer_profile_id = self.context['request'].user.get_buyer_profile().id
            
        buyer_profile = get_object_or_404(BuyerProfile,pk=buyer_profile_id)
        
        for item in data['items']:
            error = None
            
            variant = Variant.objects.filter(id=item['variant_id'], is_active=True).first()
            
            if not variant:
                unhandled_errors =  True
                
            if variant.product.allow_inventory_tracking == True and variant.product.allow_overselling == False:
                if variant.quantity < int(item['quantity']):
                    raise ValidationError({"cart": "Selcted quantities of some products no longer available."})
                # handled_errors = "Selcted quantities of some products no longer available."
            
            if unhandled_errors:
                raise serializers.ValidationError({"Data not validated.": ''})
            #Raise exxception
                        
            if not seller_id:
                seller_id = variant.product.owner_id
            elif seller_id != variant.product.owner_id:
                handled_errors = "Incorrect Data ! Sellers of all items do not match"
                
            seller_profile = get_object_or_404(SellerProfile,pk=seller_id)
            
            discount_assigned_product = buyer_profile.buyer_discounts.filter(Q(seller=seller_profile) & ~Q(product=None) & Q(is_active=True)).filter(Q(product=variant.product.id)).first()
                        
            generic_discount = buyer_profile.buyer_discounts.filter(Q(seller=seller_profile) & Q(product=None) & Q(is_active=True)).first()
                        
            buyer_discount = discount_assigned_product if discount_assigned_product else generic_discount
            
            price = float(item.get("price",variant.price))
                    
            extra_discount = min(float(item.get(
                "extra_discount",
                ((price * min(100,float(buyer_discount.discount_value))) / 100) if (buyer_discount.discount_type == "percentage") else float(buyer_discount.discount_value) if (buyer_discount.discount_type == "amount") else  0
            )),price) if buyer_discount else 0
                        
            price_after_extra_discount = (price - extra_discount)
                        
            sub_categories = list(variant.product.sub_categories.all().values_list("id",flat=True))
                        
            override_categories = [override_category for override_category in seller_profile.override_categories.filter(Q(is_active=True)).order_by("default_gst_rate") if override_category.category.id in sub_categories]
                        
            default_gst_rate = float(override_categories.pop().default_gst_rate if(len(override_categories)) else seller_profile.default_gst_rate)
                        
            gst_amount = price_after_extra_discount - (price_after_extra_discount * 100) / (default_gst_rate + 100) if seller_profile.product_price_includes_taxes else (price_after_extra_discount * default_gst_rate) / 100
            
            quantity = int(item['quantity'])
            
            item_subtotal = round(((price - gst_amount) if seller_profile.product_price_includes_taxes else price) * quantity,2)
            
            buyer_address = get_object_or_404(BuyerAddress,pk=data.get("address")) 
            
            is_order_from_same_state = True if (buyer_address.state.id == seller_profile.seller_addresses.first().state.id) else False if buyer_address else False
                        
            taxes = {"cgst":gst_amount/2,"sgst":gst_amount/2} if is_order_from_same_state else {"igst":gst_amount}  
            
            item['actual_price'] = float(item.get("actual_price", variant.actual_price))
            item['price'] =  price
            item['product_variant_id'] = item['variant_id']
            item["taxable_amount"] = round(item_subtotal - (extra_discount * quantity),2)
            item["extra_discount"] = min(price,round(extra_discount,2))
            item["igst"] = round(taxes.get("igst",0) * quantity,2)
            item["cgst"] = round(taxes.get("cgst",0) * quantity,2)
            item["sgst"] = round(taxes.get("sgst",0) * quantity,2)
            item['total_amount'] = round((item_subtotal - (extra_discount * quantity)) + (gst_amount * quantity),2)
            item['subtotal'] = item_subtotal
            
            subtotal += item_subtotal #TODO: Remove the later part after 'or', as it might never get executed

        seller = get_object_or_404(SellerProfile,pk=seller_id)
        
        taxes = dict()
        
        for item in data.get("items"):
            for key,value in item.items():
                if key not in taxes:
                    taxes[key] = 0
                
                if key in ["sgst","igst","cgst","extra_discount","taxable_amount"]:
                    taxes[key] += (float(value) * item.get('quantity',0) if(key == "extra_discount") else float(value))
        
        tax_amount = (taxes.get("igst",0) + taxes.get("cgst",0) + taxes.get("sgst",0))
        
        data["igst"] = round(taxes.get("igst",0),2)
        data["cgst"] = round(taxes.get("cgst",0),2)
        data["sgst"] = round(taxes.get("sgst",0),2)
        data["taxable_amount"] = round(taxes.get("taxable_amount",0),2)
        data["total_extra_discount"] = round(taxes.get("extra_discount",0),2)
        data['total_amount'] = round(taxes.get("taxable_amount",0)  + tax_amount,2)
        data['subtotal'] = round(subtotal,2)
        data['seller'] = seller_id

        if 'request' in self.context:
            request = self.context['request']
            data['created_by'] = request.user.id
            

        data['buyer'] = buyer_profile_id
        value = super().to_internal_value(data)
        value["items"] = data["items"]
        return value

    def create(self, validated_data): 
        # Validation TBA: Prevent any extra field in api call, like is_cancelled, created_at etc which should not be set by user api call 
        # validation TBA: check if buyer n seller are connected
        
        items = validated_data.pop('items')
        print("VDDDDD ", validated_data)
        # address = BuyerAddress.objectaddressed_data)

        if self._get_api_source() not in ['sales',"seller"] and validated_data['address'].owner_id != validated_data['buyer'].id:
            raise ValidationError({"message": "Invalid Address"})
        if self._get_api_source() == 'sales':
            validated_data['salesperson'] = self.context['request'].user.get_sales_profile()


        with transaction.atomic():
            validated_data['source'] = self._get_api_source()
            validated_data['status'] = validated_data["seller"].default_order_status
            
            validated_data["order_number"] = (f'{validated_data["seller"].order_number_prefix or ""}{validated_data["seller"].order_number_counter + 1}')
            order = Order.objects.create(**validated_data)
            
            validated_data["seller"].order_number_counter += 1
            validated_data["seller"].save()
            
            for item in items:
                variant_id = item.pop("variant_id")
                _item = OrderItem.objects.create(**item, order = order)

                product_variant = _item.product_variant
                product_variant.quantity = F('quantity') - _item.quantity
                product_variant.save()

            prev_ledger_balance = 0
            if prev_ledger := Ledger.objects.filter(buyer=order.buyer,seller=order.seller).order_by("created_at").last():
                prev_ledger_balance = prev_ledger.balance
                            
            if validated_data["seller"].default_order_status == validated_data["seller"].invoice_options.get("generate_at_status","delivered"):
                ledger,ledger_created = Ledger.objects.get_or_create(order=order,transaction_type=Ledger.TransactionTypeChoice.ORDER_CREATED,seller=order.seller,buyer=order.buyer,defaults={"balance":(prev_ledger_balance - order.total_amount),"amount":order.total_amount}) 
                
                if ledger_created:
                    invoice,invoice_created = Invoice.objects.get_or_create(order=order) 
                   
                    invoice_number = validated_data['seller'].get_invoice_prefix(invoice.id)
                    
                    invoice_name = f"{invoice_number}.pdf"
                    
                    if invoice_created:
                        invoice.invoice_number = invoice_number
                        
                        invoice_pdf = render_to_pdf('invoice/index.html',{"invoice":invoice})
                        
                        invoice.invoice_pdf.save(invoice_name, File(BytesIO(invoice_pdf.content)))
                        invoice.save()
        return order
    def update(self, instance, validated_data):
        items = validated_data.pop("items")
        order = super().update(instance, validated_data)
        
        orderitem_initial = list(instance.items.filter(is_active=True).values_list("id",flat=True))
        
        orderitem_final = []
        
        for item in items:
            # print(f" \n\n\n Order item {item} \n\n\n")
            variant_id = item.pop("variant_id")
            if item.get("id"):
                print("id is exists")
                orderitem = OrderItem(order=order,**item)
            else:
                orderitem = OrderItem.objects.create(order=order,**item)
                
            orderitem.save()

            orderitem_final.append(orderitem.id)
        
        orderitem_to_remove = [oi  for oi in orderitem_initial if oi not in orderitem_final]
        
        OrderItem.objects.filter(id__in=orderitem_to_remove).update(is_active=False)
        
        return order

class OrderListSerializer(serializers.ModelSerializer, SerializerAPISourceMixin):
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
        if all([self.api_source == 'buyer', order.status == Order.OrderStatusChoice.CANCELLED, order.cancelled_by == 'seller']):
            return 'cancelled_by_seller'
        return order.status

    short_items_description = serializers.SerializerMethodField()
    def get_short_items_description(self,order):
        DESCRIPTION_LENGTH = 60
        order_items = order.items.filter(is_active=True)
        
        first_item_variant = order_items.first().product_variant
        first_item_name = first_item_variant.product.title
        first_item_variant_description = first_item_variant.get_variant_description()
        description_text = first_item_name + (f' ({first_item_variant_description})' if first_item_variant_description else '')
        order_items_count = order_items.count()
        
        item_name_length = DESCRIPTION_LENGTH if order_items_count == 1 else (DESCRIPTION_LENGTH - 8)
        
        description_text_truncated = (description_text[:item_name_length] + '...') if len(description_text) > item_name_length else description_text
        
        if order_items_count == 1:
            return description_text_truncated
        else:
            return f'{description_text_truncated} + {order_items_count-1} more item{"s" if order_items_count>2 else ""}'

    class Meta:
        model = Order
        fields = ['id', 'order_number',"is_paid",'order_date', 'seller_name', 'items_count', 'order_status', 'total_amount', 'featured_image','short_items_description']

class SellerOrderListSerializer(OrderListSerializer):

    buyer_name = serializers.SerializerMethodField()
    def get_buyer_name(self, order):
        return order.buyer.business_name
    
    buyer_id = serializers.SerializerMethodField()
    def get_buyer_id(self,order):
        return order.buyer.id

    class Meta:
        model = Order
        fields = ['id', 'order_number', 'order_date', 'buyer_name',"buyer_id" ,'order_status', 'total_amount', 'featured_image',"short_items_description","is_paid"]

class SalespersonOrderListSerializer(OrderListSerializer):

    buyer_name = serializers.SerializerMethodField()
    def get_buyer_name(self, order):
        return order.buyer.business_name

    class Meta:
        model = Order
        fields = ['id', 'order_date', 'buyer_name', 'order_status', 'total_amount', 'featured_image',]

class OrderHistorySerializer(serializers.ModelSerializer):

    created_by_user = serializers.SerializerMethodField()
    def get_created_by_user(self, instance):
        return instance.created_by.name

    created_by_entity = serializers.SerializerMethodField()
    def get_created_by_entity(self, instance):
        if instance.seller:
            return instance.seller.business_name
        elif instance.buyer:
            return instance.buyer.business_name
        elif instance.salesperson:
            return instance.salesperson.business_name

    time = serializers.SerializerMethodField()
    def get_time(self, instance):
        return instance.created_at.astimezone().strftime('%H:%M %p')

    date = serializers.SerializerMethodField()
    def get_date(self, instance):
        return instance.created_at.astimezone().strftime('%h %d, %Y')

    class Meta:
        model = OrderHistory
        fields = ['status', 'created_by_user', 'created_by_entity', 'time', 'date']

class StatusVariableValueSerializer(serializers.ModelSerializer):
    
    variable_name = serializers.SerializerMethodField()
    def get_variable_name(self, instance):
        return instance.variable.name

    variable_slug = serializers.SerializerMethodField()
    def get_variable_slug(self, instance):
        return instance.variable.slug

    status = serializers.SerializerMethodField()
    def get_status(self, instance):
        return "dispatched"

    is_internal = serializers.SerializerMethodField()
    def get_is_internal(self, instance):    # TODO: Security - Don;t send variable to non-accessible people (like, don't send internal variables to buyers) 
        return instance.variable.is_internal
        
    class Meta:
        model = OrderStatusVariableValue
        fields = ["id", 'status', 'variable_name', 'value', 'variable_slug', 'is_internal']

class OrderDetailsSerializer(SellerOrderListSerializer):

    address = BuyerAddressSerializer()
    
    items = serializers.SerializerMethodField()
    def get_items(self,order):
        return OrderItemSerializer(order.items.filter(is_active=True),many=True).data
    
    invoice = serializers.SerializerMethodField()
    
    
    history = OrderHistorySerializer(many=True)
    order_time = serializers.SerializerMethodField()
    buyer_name = serializers.SerializerMethodField()
    buyer_business_name = serializers.SerializerMethodField()
    created_by_user = serializers.SerializerMethodField()
    created_by_entity = serializers.SerializerMethodField()
    status_variable_values = serializers.SerializerMethodField()
    # address_id = serializers.Serializer.SerializerMethodField()
    
    # def get_address_id(self,order):
    #     return order.address

    def get_order_date(self, order):
        return order.created_at.astimezone().strftime("%b %d, %Y")
    
    def get_order_time(self, order):
        return order.created_at.astimezone().strftime('%H:%M %p')

    def get_buyer_name(self,order):
        name = order.buyer.owner.name if order.buyer.owner else ""
        return name
    
    def get_buyer_business_name(self,order):
        return order.buyer.business_name
    def get_created_by_user(self, order):
        return order.created_by.name
    
    def get_created_by_entity(self, order):
        if order.salesperson:
            return order.salesperson.seller.business_name
        else:
            return order.buyer.business_name
        
    def get_invoice(self,order):    
        return GenerateInvoiceSerializer(order.invoices.first()).data

    def get_status_variable_values(self, order):
        return StatusVariableValueSerializer(order.status_variable_values.all(), many=True).data
    
    buyer = BuyerShortDetailSerializer()
    
    def to_representation(self, instance):
        output = super(OrderDetailsSerializer, self).to_representation(instance)
        output["cgst"] = float(instance.cgst)
        output["sgst"] = float(instance.sgst)
        output["igst"] = float(instance.igst)
        output["taxable_amount"] = float(instance.taxable_amount)
        output["total_amount"] = float(instance.total_amount)
        output["total_extra_discount"] = float(instance.total_extra_discount)
        output["subtotal"] = float(instance.subtotal)
        return output

    class Meta:
        model = Order
        fields=['order_number', 'order_date', 'order_time','seller_name', 'buyer_name','buyer_business_name',"buyer_id" ,'order_status','taxable_amount','sgst','cgst','igst', 'total_amount',"total_extra_discount","subtotal",'items', "invoice",'address', 'history', 'created_by_user', 'created_by_entity', 'status_variable_values','buyer',"tax_amount","is_paid"]
        
class GenerateInvoiceSerializer(serializers.ModelSerializer):
    
    def create(self, validated_data):
        with transaction.atomic():
            invoice,created = Invoice.objects.get_or_create(**validated_data)
            
            prefix = self.context["request"].user.seller_profiles.first().invoice_prefix
            
            invoice_number = f'{prefix}{invoice.id}/21-22' if prefix else f'{invoice.id}/21-22'
            
            invoice_name = f"{invoice_number}.pdf"
            
            if created: 
                invoice.invoice_number = invoice_number
                
                invoice_pdf = render_to_pdf('invoice/index.html',{"invoice":invoice})
                
                invoice.invoice_pdf.save(invoice_name, File(BytesIO(invoice_pdf.content)))
                    
                invoice.save()
            
            return invoice
    
    class Meta:
        model = Invoice
        fields = ["id","order","invoice_number","invoice_pdf","created_at"]
        
class PaymentShortDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id","amount","mode","remarks","date"]
        
class OrderShortDetailSerializer(serializers.ModelSerializer):
    
    created_by = serializers.SerializerMethodField()
    def get_created_by(self,order):
        return {"userId":order.created_by.id,"username":order.created_by.username}
    
    class Meta:
        model = Order
        fields = ["id",'order_number',"created_by","status","is_paid"]
        extra_kwargs = {
            "created_by":{
                "read_only":True
            }
        }
        
class LedgerSerializer(serializers.ModelSerializer):
    
    description = serializers.SerializerMethodField()
    def get_description(self,ledger):
        return ledger.description
    
    
    payment = PaymentShortDetailSerializer()
    order = OrderShortDetailSerializer()
    
    
    class Meta:
        model = Ledger
        fields = ["id","transaction_type","amount","balance","payment","order","description","created_at"]
        
class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["seller","buyer","amount","mode","remarks"]
        extra_kwargs={
            "seller":{
                "required":False
            }
        }
        
    def create(self, validated_data):
        with transaction.atomic():
            buyer = validated_data.get("buyer")
            seller = validated_data.get("seller")
            amount = validated_data.get("amount")
            
            payment = Payment.objects.create(**validated_data)
            
            prev_ledger_balance = 0
            if previous_ledger := Ledger.objects.filter(seller=seller,buyer=buyer).order_by("created_at").last():
                prev_ledger_balance = previous_ledger.balance
                
            new_ledger = Ledger.objects.create(transaction_type=Ledger.TransactionTypeChoice.PAYMENT_ADDED,amount=amount,balance=(payment.amount + prev_ledger_balance),payment=payment,buyer=buyer,seller=seller)
            
        return payment
    
class OrderStatusVariableSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderStatusVariableValue
        fields = ["id","value","order","variable"]
        extra_kwargs = {
            "order":{
                "read_only":True
            },
            "variable":{
                "read_only":True
            }
        }
        
class InvoiceTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvoiceTemplate
        fields = ['id','name','slug','image_url']
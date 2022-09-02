from django.db.models import Q,Count,Sum,Min,Max,Prefetch
from django.db import transaction
from django.shortcuts import render,get_object_or_404
from rest_framework import generics, mixins
from rest_framework.views import APIView
from .models import Order, OrderHistory, OrderStatusVariableValue,Payment
from .serializers import *
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved, IsFromSellerAPI
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from supplyr.utils.api.mixins import APISourceMixin
from django.db.models import F
from rest_framework import status
from supplyr.profiles.models import *
from rest_framework.generics import RetrieveAPIView
from supplyr.inventory.serializers import ProductListSerializer
from supplyr.inventory.models import Product,ProductImage


class OrderView(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView,mixins.UpdateModelMixin):
    """
    List, create, retrieve and cancel orders from buyer app
    """
    # queryset = BuyerAddress.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        return Order.objects.all()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print(" ----- requested data ------ ",request.data)
        if pk := kwargs.get("pk"):
            order = get_object_or_404(Order,pk=pk,seller=self.request.user.seller_profiles.first())
            if order.status not in ["processed",'cancelled','dispatched','delivered']:
                return self.update(request,*args,**kwargs)
            else:
                return Response({"message":"Your are not allowed to update this order"},status=status.HTTP_304_NOT_MODIFIED)
        return self.create(request, *args, **kwargs)

class ProductDetailView(RetrieveAPIView):
    permission_classes = [IsApproved]
    serializer_class = ProductListSerializer
    
    def get_queryset(self):
        profile = self.request.user.seller_profiles.first()
        return Product.objects.filter(owner = profile, is_active = True)\
            .annotate(
                variants_count_annotated=Count('variants', filter=Q(variants__is_active=True)),
                quantity_all_variants=Sum('variants__quantity', filter=Q(variants__is_active=True)),
                sale_price_minimum=Min('variants__price', filter=Q(variants__is_active=True)),
                sale_price_maximum=Max('variants__price', filter=Q(variants__is_active=True))
                )\
            .prefetch_related(
                 Prefetch('images', queryset=ProductImage.objects.filter(is_active=True), to_attr='active_images_prefetched'),
                 Prefetch('variants', queryset=Variant.objects.filter(is_active=True), to_attr='active_variants_prefetched'),
                 )


class GenerateInvoiceView(generics.GenericAPIView,mixins.CreateModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Invoice.objects.filter(is_active=True)
    serializer_class = GenerateInvoiceSerializer
    
    # def perform_create(self, serializer):
    #     invoice = serializer.save()
    #     seller_prefix = self.request.user.seller_profiles.first().prefix
    #     invoice.invoice_number = f'{seller_prefix}{invoice.id}'
    #     invoice.save()
    #     return invoice
    
    def post(self,request,*args,**kwargs):
        return self.create(request,*args,**kwargs)

class OrderListView(mixins.ListModelMixin, generics.GenericAPIView, APISourceMixin):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.api_source == 'seller':
            return SellerOrderListSerializer
        elif self.api_source == 'sales':
            return SalespersonOrderListSerializer
        return OrderListSerializer

    def get_queryset(self):
        filters = {}
        if status_filter := self.request.GET.get('order_status'):
            filters['status'] = status_filter

        if self.api_source == 'seller':
            filters['seller'] = self.request.user.get_seller_profile()
        elif self.api_source == 'buyer':
            filters['buyer'] = self.request.user.get_buyer_profile()
        elif self.api_source == 'sales':
            filters['salesperson'] = self.request.user.get_sales_profile()

        return Order.objects.filter(**filters).order_by('-created_at')

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class OrderDetailsView(generics.RetrieveAPIView):
    serializer_class = OrderDetailsSerializer
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()


class OrdersBulkUpdateView(APIView):
    permission_classes = [IsApproved, IsFromSellerAPI]

    def post(self, request, *args, **kwargs):
        operation = request.data.get('operation')
        profile = request.user.seller_profiles.first()

        order_ids = request.data.get('order_ids')

        if operation in ['change_status', 'change_status_with_variables']:
            data = request.data.get('data')
            
            new_status = data['status'] if operation == 'change_status_with_variables' else data

            # if new_status not in Order.OrderStatusChoice.choices:
            #     return Response({'success': False, 'message': 'Invalid Status'})
            
            order_filters = [option["slug"] for option in profile.order_status_options if new_status in option["transitions_possible"]]
            
            print(" ----- Order Filters ----- ",order_filters)
            
            orders = Order.objects.filter(pk__in = order_ids, seller=profile, is_active=True,status__in=order_filters).exclude(status__in=[Order.OrderStatusChoice.CANCELLED, new_status])

            with transaction.atomic():
                _orders = list(orders)  # As the 'orders' queryset will remove the current orders after getting updated below, and no orders will be there because of status=new_status exclusion. Hence made a list to retain fetched orders list, to add history entry
                orders.update(status = new_status)
                for order in _orders:
                    OrderHistory.objects.create(order = order, status = new_status, created_by = request.user, seller = profile)
                    
                    ######## ----- Ledger Start ----- ########
                    prev_ledger_balance = 0
                    if prev_ledger := Ledger.objects.filter(buyer=order.buyer,seller=order.seller).order_by("created_at").last():
                            prev_ledger_balance = prev_ledger.balance
                            
                    if new_status == profile.invoice_options.get("status","processed"):
                        ledger,created = Ledger.objects.get_or_create(order=order,transaction_type=Ledger.TransactionTypeChoice.ORDER_CREATED,seller=order.seller,buyer=order.buyer,amount=order.total_amount,balance=(prev_ledger_balance - order.total_amount ))
                        
                    elif new_status == Order.OrderStatusChoice.CANCELLED:
                        ledger,created = Ledger.objects.get_or_create(order=order,transaction_type=Ledger.TransactionTypeChoice.ORDER_CANCELLED,seller=order.seller,buyer=order.buyer,amount=order.total_amount,balance=(prev_ledger_balance + order.total_amount ))
                    ######## ----- Ledger End ----- ########

                if operation == 'change_status_with_variables':
                    variables = data['variables']
                    for order in _orders:
                        for variable_id in variables.keys():
                            OrderStatusVariableValue.objects.update_or_create(variable_id = variable_id, order = order, defaults = {'value': variables[variable_id]})

        return Response({'success': True})

class OrderCancellationView(APIView, APISourceMixin):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')


        order = Order.objects.filter(id=order_id).exclude(Q(status=Order.OrderStatusChoice.CANCELLED) | Q(status=Order.OrderStatusChoice.DELIVERED) | Q(is_active=False))
        order_history_kwargs = {}
        if self.api_source == 'buyer':
            buyer_profile = self.request.user.get_buyer_profile()
            order = order.filter(buyer = buyer_profile).first()
            order_history_kwargs['buyer'] = buyer_profile
        elif self.api_source == 'seller':
            seller_profile = self.request.user.get_seller_profile()
            order = order.filter(seller =seller_profile).first()
            order_history_kwargs['seller'] = seller_profile
        elif self.api_source == 'sales':
            salesperson_profile = self.request.user.get_sales_profile()
            order = order.filter(salesperson = salesperson_profile).first()
            order_history_kwargs['sales'] = salesperson_profile

        if order:
            with transaction.atomic():
                order.status = Order.OrderStatusChoice.CANCELLED
                order.cancelled_by = self.api_source
                order.save()
                OrderHistory.objects.create(order = order, status = Order.OrderStatusChoice.CANCELLED, created_by = request.user, **order_history_kwargs)
                
                ######## ----- Ledger Start ----- ########
                
                prev_ledger_balance = 0
                if prev_ledger := Ledger.objects.filter(buyer=order.buyer,seller=order.seller).order_by("created_at").last():
                    prev_ledger_balance = prev_ledger.balance
                    
                ledger = Ledger.objects.create(transaction_type=Ledger.TransactionTypeChoice.ORDER_CANCELLED,seller=order.seller,buyer=order.buyer,amount=order.total_amount,balance=(prev_ledger_balance + order.total_amount ),order=order)
                
                ######## ----- Ledger End ----- ########

                for item in order.items.all():
                    product_variant = item.product_variant
                    product_variant.quantity = F('quantity') + item.quantity
                    product_variant.save()
                
        else:
            return Response({'success': False}, status=404)

            # TODO: Increase quantity in inventory

        order_data = OrderDetailsSerializer(order).data

        return Response({'success': True, 'order_data': order_data})


class PaymentCreateAPIView(generics.GenericAPIView,mixins.CreateModelMixin):
    serializer_class = PaymentSerializer
    permission_classes = [IsApproved]
    
    def get_queryset(self):
        return  Payment.objects.filter(seller=self.request.user.seller_profiles.first(),is_active=True)
    
    def perform_create(self, serializer):
        serializer.save(seller=self.request.user.seller_profiles.first())
        
    def post(self,request,*args,**kwargs):
        return self.create(request,*args,**kwargs)
    
class LedgerAPIView(generics.GenericAPIView,mixins.ListModelMixin):
    serializer_class = LedgerSerializer
    permission_classes = [IsApproved]
    
    def get_queryset(self):
        return  Ledger.objects.filter(seller=self.request.user.seller_profiles.first(),buyer=self.kwargs.get("pk")).order_by("-created_at")

    def get(self,request,*args,**kwargs):
        return self.list(request,*args,**kwargs)
    
class OrderStatusVariableAPIView(generics.GenericAPIView,mixins.UpdateModelMixin):
    serializer_class = OrderStatusVariableSerializer
    permission_classes = [IsApproved]
    
    def get_queryset(self):
        seller = self.request.user.seller_profiles.first()
        order = get_object_or_404(Order,pk=self.kwargs.get("orderId"),seller=seller)
        return OrderStatusVariableValue.objects.filter(order=order)
    
    def put(self, request,*args,**kwargs):
        return self.partial_update(request,*args,**kwargs)
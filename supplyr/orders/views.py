from django.db.models import Q,Count,Sum,Min,Max,Prefetch
from django.db import transaction
from django.shortcuts import render,get_object_or_404
from rest_framework import generics, mixins
from rest_framework.views import APIView
# from .models import Order, OrderHistory, OrderStatusVariableValue,Payment,OrderShortDetailSerializer
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
from supplyr.core.app_config import ADD_LEDGER_ENTRY_ON_MARK_ORDER_PAID
from supplyr.core.functions import render_to_pdf
from io import BytesIO
from django.core.files import File

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
        if pk := kwargs.get("pk"):
            order = get_object_or_404(Order,pk=pk,seller=self.request.user.seller_profiles.first())
            if order.status not in ["processed",'cancelled','dispatched','delivered']:
                return self.update(request,*args,**kwargs)
            else:
                return Response({"message":"Your are not allowed to update this order"},status=status.HTTP_304_NOT_MODIFIED)
        return self.create(request, *args, **kwargs)

class MarkAsOrderPaidView(APIView):
    permission_classes = [IsApproved]
    
    def put(self,request,*args,**kwargs):
            with transaction.atomic():
                seller = request.user.seller_profiles.first()
                instance = get_object_or_404(Order,pk=kwargs.get("pk"))
                serializer = OrderShortDetailSerializer(instance,request.data,partial=True)
                 
                if serializer.is_valid():
                    serializer.save()
                    if ADD_LEDGER_ENTRY_ON_MARK_ORDER_PAID:
                        prev_ledger_balance = 0
                        if prev_ledger := Ledger.objects.filter(buyer=instance.buyer,seller=instance.seller).order_by("created_at").last():
                            prev_ledger_balance = prev_ledger.balance
                        ledger,created = Ledger.objects.get_or_create(order=instance,transaction_type=Ledger.TransactionTypeChoice.ORDER_PAID,seller=seller,buyer=instance.buyer,defaults={"amount":instance.total_amount,"balance":(prev_ledger_balance + instance.total_amount )})
                        
                        if created:
                            payment = Payment.objects.create(seller=seller,buyer=instance.buyer,amount=instance.total_amount,mode=Payment.PaymentMode.BankTransfer,remarks="Order Marked as Paid")
                    
                            ledger.payment = payment
                            
                            ledger.save()
                            
                    return Response({"message":"Success"},status=status.HTTP_202_ACCEPTED)
                return Response(serializer.errors)

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
        print(" Requested Data ",request.data)
        # return Response(" Hello World ")
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

class OrderDetailsView(generics.GenericAPIView,mixins.RetrieveModelMixin):
    permission_classes = [IsAuthenticated]
    queryset = Order.objects.all()
    
    def get_serializer_class(self):
        return OrderDetailsSerializer
    
    def get(self,request,*args,**kwargs):
        return self.retrieve(request,*args,**kwargs)

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
            
            
            orders = Order.objects.filter(pk__in = order_ids, seller=profile, is_active=True,status__in=order_filters).exclude(status__in=[new_status])
            

            with transaction.atomic():
                _orders = list(orders)  # As the 'orders' queryset will remove the current orders after getting updated below, and no orders will be there because of status=new_status exclusion. Hence made a list to retain fetched orders list, to add history entry
                orders.update(status = new_status)
                
                for order in _orders:
                    OrderHistory.objects.create(order = order, status = new_status, created_by = request.user, seller = profile)
                    
                    ######## ----- Ledger Start ----- ########
                    prev_ledger_balance = 0
                    if prev_ledger := Ledger.objects.filter(buyer=order.buyer,seller=order.seller).order_by("created_at").last():
                            prev_ledger_balance = prev_ledger.balance
                            
                    if new_status == profile.invoice_options.get("generate_at_status","delivered"):
                        ledger,ledger_created = Ledger.objects.get_or_create(order=order,transaction_type=Ledger.TransactionTypeChoice.ORDER_CREATED,seller=order.seller,buyer=order.buyer,defaults={"amount":order.total_amount,"balance":(prev_ledger_balance - order.total_amount )})
                        
                        if ledger_created:
                            invoice,invoice_created = Invoice.objects.get_or_create(order=order) 
                                       
                            invoice_number = profile.get_invoice_prefix(invoice.id)
                    
                            invoice_name = f"{invoice_number}.pdf"
                    
                            if invoice_created:
                                invoice.invoice_number = invoice_number
                                
                                invoice_pdf = render_to_pdf('invoice/index.html',{"invoice":invoice})
                                
                                invoice.invoice_pdf.save(invoice_name, File(BytesIO(invoice_pdf.content)))
                                
                                invoice.save()
                    
                    elif new_status == Order.OrderStatusChoice.CANCELLED or new_status == Order.OrderStatusChoice.RETURNED:
                        transaction_type = Ledger.TransactionTypeChoice.ORDER_CANCELLED if (Ledger.TransactionTypeChoice.ORDER_CANCELLED == new_status) else Ledger.TransactionTypeChoice.ORDER_RETURNED


                        ledger = Ledger.objects.create(order=order,transaction_type=transaction_type,seller=order.seller,buyer=order.buyer,amount=order.total_amount,balance=(prev_ledger_balance + order.total_amount))
                    ######## ----- Ledger End ----- ########

                if operation == 'change_status_with_variables':
                    variables = data['variables']
                    for order in _orders:
                        for variable_id in variables.keys():
                            OrderStatusVariableValue.objects.update_or_create(variable_id = variable_id, order = order, defaults = {'value': variables[variable_id]})

        return Response({'success': True})

class BulkUpdateOrderItemsView(APIView):
    permission_classes = [IsFromSellerAPI]
    
    def post(self,request,*args,**kwargs):
        print(" Requested Data ",request.data)
        
        profile = request.user.seller_profiles.first()
        
        order = get_object_or_404(Order,pk=self.kwargs.get("orderId"),seller=profile)
        
        data = request.data.get('data')
        
        order_ids = data["order_ids"]
        
        status = data["status"]
        
        operation = request.data.get("operation")
        
        filters = [option["slug"] for option in profile.order_status_options if status in option["transitions_possible"]]
        
        with transaction.atomic():
            orderitems = None
            
            order_group = None
          
            initial_orderitems = OrderItem.objects.filter(id__in=order_ids)
            
            print(" initial orderitems ",initial_orderitems)
            
            if operation in ['change_status', 'change_status_with_variables']:
                orderitems = initial_orderitems.filter(Q(status__in=filters) | Q(order_group__status__in=filters))
                
                option = profile.order_status_options[[option["slug"] for option in profile.order_status_options].index(status)]
                
                if option["editing_allowed"]:
                    for orderitem in orderitems:
                        if orderitem_ordergroup := orderitem.order_group:
                            
                            variables = OrderStatusVariableValue.objects.filter(order_group=orderitem_ordergroup)
                            
                            for variable in variables:
                                
                                variable.delete()
                                
                        orderitem.status = status
                        
                        orderitem.order_group = None 
                        
                        orderitem.save()   
                else:    
                    group = order.groups.last()
                        
                    orderitem_ordergroup = orderitems.first().order_group.id if orderitems.first().order_group else None
                        
                    group_index = orderitems.first().order_group.group_index if orderitems.first().order_group else  int(group.group_index) + 1 if group else 1
                        
                    order_group,created = OrderGroup.objects.update_or_create(parent=order,group_index=group_index,defaults={"status":status})
                    
                    for orderitem in orderitems:
                        
                        orderitem.order_group = order_group
                        
                        orderitem.save()
                    
                    
                ######## ----- Ledger Start ----- ########
                prev_ledger_balance = 0
                if prev_ledger := profile.ledgers.filter(buyer=order.buyer).last():
                    prev_ledger_balance = prev_ledger.balance
                      
                generate_ledger_on_status = option.get("slug") if not option.get("editing_allowed") else profile.invoice_options.get("generate_at_status")
                    
                if status == generate_ledger_on_status:
                    ledger,created = Ledger.objects.get_or_create(order=order,order_group=order_group,transaction_type=Ledger.TransactionTypeChoice.ORDER_CREATED,seller=order.seller,buyer=order.buyer,amount=order.total_amount,balance=(prev_ledger_balance - order.total_amount ))
                    
                elif status == Order.OrderStatusChoice.CANCELLED or status == Order.OrderStatusChoice.RETURNED:
                    balance = (prev_ledger_balance + total_amount) if True else (prev_ledger_balance - total_amount)
                        
                    ledger,created = Ledger.objects.get_or_create(order=order,transaction_type=Ledger.TransactionTypeChoice.ORDER_CANCELLED,seller=order.seller,buyer=order.buyer,amount=total_amount,balance=balance)

                ######## ----- Ledger End ----- ########
                
                orderhistory = OrderHistory.objects.create(order=order,order_group=order_group, status = status, created_by = request.user, seller = profile)
                
                for orderitem in orderitems:
                    orderhistory.items.add(orderitem)
                    
                items = OrderItem.objects.filter(order=order)
                
                if order.is_global_fulfillment:
                    order.status = status
                    order.save()
                    
                if operation == "change_status_with_variables":
                    variables = data["variables"]
                    
                    for variable_id in variables.keys():
                        OrderStatusVariableValue.objects.update_or_create(variable_id = variable_id, order = order,order_group=order_group, defaults = {'value': variables[variable_id]})
        
        return Response({"message":"success","status":201})

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
        print(" Requested Data ",request.data)
        return self.partial_update(request,*args,**kwargs)

class InvoiceTemplateView(generics.GenericAPIView,mixins.ListModelMixin):
    permission_classes = [IsApproved]
    serializer_class = InvoiceTemplateSerializer
    queryset = InvoiceTemplate.objects.all()
    pagination_class = None
    
    def get(self,request,*args,**kwargs):
        return self.list(request,*args,**kwargs)
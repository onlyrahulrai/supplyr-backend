from django.db.models import Q
from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer, OrderListSerializer, OrderDetailsSerializer, SellerOrderListSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved, IsFromSellerAPI
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from supplyr.utils.api.mixins import APISourceMixin
from django.db.models import F

class OrderView(mixins.ListModelMixin,
                  mixins.CreateModelMixin,
                  generics.GenericAPIView):
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
        return self.create(request, *args, **kwargs)

    # def get_queryset(self):
    #     profile = self.request.user.buyer_profiles.first()
    #     return BuyerAddress.objects.filter(is_active=True, owner = profile).order_by('-is_default')

    # def perform_create(self, serializer):
    #     owner = self.request.user.buyer_profiles.first()
    #     serializer.save(owner = owner)
    
    # def perform_destroy(self, instance):
    #     instance.is_active = False
    #     instance.save()


class OrderListView(mixins.ListModelMixin, generics.GenericAPIView, APISourceMixin):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.api_source == 'seller':
            return SellerOrderListSerializer
        return OrderListSerializer

    def get_queryset(self):
        filters = {}
        if status_filter := self.request.GET.get('order_status'):
            filters['status'] = status_filter

        if self.api_source == 'seller':
            filters['seller'] = self.request.user.get_seller_profile()
        elif self.api_source == 'buyer':
            filters['buyer'] = self.request.user.get_buyer_profile()

        return Order.objects.order_by('-created_at').filter(**filters)

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

        if operation == 'change_status':
            new_status = request.data.get('data')
            Order.objects.filter(pk__in = order_ids, seller=profile, is_active=True).exclude(status=Order.OrderStatusChoice.CANCELLED)\
                            .update(status = new_status)

        return Response({'success': True})

class OrderCancellationView(APIView, APISourceMixin):
    
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        order_id = request.data.get('order_id')


        order = Order.objects.filter(id=order_id).exclude(Q(status=Order.OrderStatusChoice.CANCELLED) | Q(status=Order.OrderStatusChoice.DELIVERED) | Q(is_active=False))
        if self.api_source == 'buyer':
            buyer_profile = self.request.user.get_buyer_profile()
            order = order.filter(buyer = buyer_profile).first()
        elif self.api_source == 'seller':
            seller_profile = self.request.user.get_seller_profile()
            order = order.filter(seller =seller_profile).first()

        if order:
            order.status = Order.OrderStatusChoice.CANCELLED
            if self.api_source in ['seller', 'buyer']:
                order.cancelled_by = self.api_source
            order.save()

            for item in order.items.all():
                product_variant = item.product_variant
                product_variant.quantity = F('quantity') + item.quantity
                product_variant.save()
                
        else:
            return Response({'success': False}, status=404)

            # TODO: Increase quantity in inventory

        order_data = OrderDetailsSerializer(order).data

        return Response({'success': True, 'order_data': order_data})



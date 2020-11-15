from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer, OrderListSerializer, OrderDetailsSerializer, SellerOrderListSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved, IsFromSellerAPI
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from supplyr.utils.api.mixins import APISourceMixin

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

        # if operation in ['add-subcategories', 'remove-subcategories']:
        #     product_ids = request.data.get('product_ids')
        #     sub_categories_list = request.data.get('data')

        #     for product in Product.objects.filter(pk__in = product_ids, owner=profile, is_active = True):
        #         if operation == 'add-subcategories':
        #             product.sub_categories.add(*sub_categories_list)
        #         else:
        #             product.sub_categories.remove(*sub_categories_list)
        
        return Response({'success': True})

from django.shortcuts import render
from rest_framework import generics, mixins
from rest_framework.views import APIView
from .models import Order
from .serializers import OrderSerializer, OrderListSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved
from rest_framework.permissions import IsAuthenticated

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


class OrderListView(mixins.ListModelMixin, generics.GenericAPIView):
    serializer_class = OrderListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter()

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)
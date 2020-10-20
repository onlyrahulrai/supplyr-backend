from django.shortcuts import render
from rest_framework import generics, mixins
from .models import BuyerAddress
from .serializers import BuyerAddressSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved

class AddressView(generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView):
    """
    List, add and edit addresses from buyer app
    """
    # queryset = BuyerAddress.objects.all()
    serializer_class = BuyerAddressSerializer
    permission_classes = [IsFromBuyerAPI]
    pagination_class = None

    def get_queryset(self):
        profile = self.request.user.buyer_profiles.first()
        return BuyerAddress.objects.filter(is_active=True, owner = profile)

    def perform_create(self, serializer):
        owner = self.request.user.buyer_profiles.first()
        serializer.save(owner = owner)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
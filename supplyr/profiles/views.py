from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, mixins, views
from .models import BuyerAddress, BuyerSellerConnection
from .serializers import BuyerAddressSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved
from supplyr.utils.api.mixins import APISourceMixin
from supplyr.inventory.serializers import SellerShortDetailsSerializer
from supplyr.core.models import SellerProfile
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

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
        return BuyerAddress.objects.filter(is_active=True, owner = profile).order_by('-is_default')

    def perform_create(self, serializer):
        owner = self.request.user.buyer_profiles.first()
        serializer.save(owner = owner)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class SellerView(views.APIView, APISourceMixin):

    permission_classes = [IsAuthenticated, IsFromBuyerAPI]

    def post(self, request, *args, **kwargs):
        code = request.data['connection_code']
        print(code)
        if seller := SellerProfile.objects.filter(connection_code__iexact = code, is_active= True, is_approved=True).first():
            BuyerSellerConnection.objects.get_or_create(seller=seller, is_active=True, buyer = self.request.user.get_buyer_profile())
            return Response({'success': True})
        else:
            return Response({
                'message': 'Invalid connection code'
            }, status=400)

    def delete(self, request, *args, **kwargs):
        seller_id = kwargs.get('pk')
        buyer_profile = self.request.user.get_buyer_profile()
        connection = BuyerSellerConnection.objects.filter(seller_id=seller_id, buyer = buyer_profile, is_active = True).first()
        if connection:
            connection.is_active = False
            connection.deactivated_at = timezone.now()
            connection.save()

        return Response({'success': True})

class SellersListView(generics.ListAPIView):
    permission_classes = [IsFromBuyerAPI]
    serializer_class = SellerShortDetailsSerializer
    pagination_class = None
    # queryset = SellerProfile.objects.all()
    def get_queryset(self):
        buyer_profile = self.request.user.get_buyer_profile()
        return SellerProfile.objects.filter(connections__buyer=buyer_profile, is_active=True, connections__is_active=True)
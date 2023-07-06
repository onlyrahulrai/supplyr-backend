from django.shortcuts import render,get_object_or_404
from django.db.models import Q
from django.http import HttpResponse
from rest_framework.generics import ListAPIView, GenericAPIView, RetrieveAPIView
from rest_framework import mixins
from supplyr.core.permissions import IsApproved, IsFromSellerAPI
from rest_framework.response import Response
from .utils import CustomPageNumberPagination
from .serializers import (
    BuyerDiscountSerializer,
    SellerContactWithBuyerSerializer, 
    SellerContactWithBuyerDetailSerializer, 
    DiscountAssignedProductSerializer
)
from supplyr.inventory.models import BuyerDiscount
from .serializers import *
# Create your views here.


class SellerContactWithBuyersAPIView(GenericAPIView, mixins.ListModelMixin):
    permission_classes = [IsApproved, IsFromSellerAPI]
    serializer_class = SellerContactWithBuyerSerializer
    pagination_class = CustomPageNumberPagination

    def get_queryset(self):
        query = self.request.GET.get("search", None)
        seller = self.request.user.seller_profiles.first()
        if(query):
            buyers = seller.connections.filter((Q(buyer__business_name__icontains=query) | Q(
                buyer__owner__email__icontains=query) | Q(buyer__owner__mobile_number__icontains=query)) & Q(is_active=True))
        else:
            buyers = seller.connections.filter(is_active=True)
        return buyers

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)

class SellerContactWithBuyerDetailAPIView(GenericAPIView, mixins.RetrieveModelMixin):
    permission_classes = [IsApproved, IsFromSellerAPI]
    serializer_class = SellerContactWithBuyerDetailSerializer
    lookup_field = "buyer"

    def get_queryset(self):
        seller = self.request.user.seller_profiles.first()
        return seller.connections.filter(is_active=True)

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)

class BuyerDiscountAPIView(GenericAPIView, mixins.CreateModelMixin,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,mixins.DestroyModelMixin):
    permission_classes = [IsApproved, IsFromSellerAPI]
    serializer_class = BuyerDiscountSerializer
    queryset = BuyerDiscount.objects.filter(is_active=True)
        
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()
                
    def get(self,request,*args,**kwargs):
        return self.retrieve(request,*args,**kwargs)
        
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            seller = self.request.user.seller_profiles.first()
            instance = serializer.save(seller=seller)
             
            key = "discount_assigned_products" if(instance.product) else "generic_discount"
             
            value = DiscountAssignedProductSerializer(instance.buyer.buyer_discounts.filter(Q(seller=seller) & ~Q(product=None) & Q(is_active=True)),many=True).data if(instance.product) else serializer.data
            
            return Response({key:value})
        return Response(serializer.error)
    
    def put(self,request,*args,**kwargs):
        instance = get_object_or_404(BuyerDiscount,pk=kwargs.get("pk"))
        
        serializer = self.serializer_class(instance,data=request.data,partial=True)
        
        if serializer.is_valid():
            instance = serializer.save()
            
            seller = self.request.user.seller_profiles.first()
             
            key = "discount_assigned_products" if(instance.product) else "generic_discount"
             
            value = DiscountAssignedProductSerializer(instance.buyer.buyer_discounts.filter(Q(seller=seller) & ~Q(product=None) & Q(is_active=True)),many=True).data if(instance.product) else serializer.data
            
            return Response({key:value})
        return Response(serializer.errors)
    
    def delete(self,request,*args,**kwargs):
        instance = BuyerDiscount.objects.get(id=kwargs.get("pk")) 
        
        serializer = self.serializer_class(instance,data={"is_active":False})
        
        if serializer.is_valid():
            instance = serializer.save()
            
            seller = self.request.user.seller_profiles.first()
             
            key = "discount_assigned_products" if(instance.product) else "generic_discount"
             
            value = DiscountAssignedProductSerializer(instance.buyer.buyer_discounts.filter(Q(seller=seller) & ~Q(product=None) & Q(is_active=True)),many=True).data if(instance.product) else 0
            
            return Response({key:value})
        return Response(serializer.error)

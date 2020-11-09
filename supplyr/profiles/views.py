from django.shortcuts import render
from django.utils import timezone
from rest_framework import generics, mixins, views
from .models import BuyerAddress, BuyerSellerConnection, SellerProfile, BuyerProfile
from .serializers import BuyerAddressSerializer, BuyerProfileSerializer, SellerProfilingSerializer, SellerProfilingDocumentsSerializer, SellerShortDetailsSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsApproved, IsUnapproved
from supplyr.utils.api.mixins import APISourceMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from supplyr.utils.api.mixins import UserInfoMixin


class BuyerProfilingView(views.APIView, UserInfoMixin):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data.copy()
        data['owner'] = request.user.pk
        
        existing_profile = BuyerProfile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = BuyerProfileSerializer(existing_profile, data = data)
        else:
            serializer = BuyerProfileSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            serializer_data = self.inject_user_info(serializer.data, request.user)
            
            request.user.add_to_buyers_group()
            return Response(serializer_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SellerProfilingView(views.APIView, UserInfoMixin):
    permission_classes = [IsUnapproved]

    def post(self, request, *args, **kwargs):
        # if(request.user.is_approved):
        #     return Response("User Already Approved", status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data['owner'] = request.user.pk
        
        existing_profile = SellerProfile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = SellerProfilingSerializer(existing_profile, data = data)
        else:
            serializer = SellerProfilingSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            serializer_data = self.inject_user_info(serializer.data, request.user)

            if not existing_profile:
                existing_profile = SellerProfile.objects.filter(owner=request.user).first()
            existing_profile.generate_connection_code()  #Will be generated only if no code exists (check is inside function)
                
            return Response(serializer_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ProfilingDocumentsUploadView(views.APIView):    #Seller
    
    permission_classes = [IsUnapproved]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        
        data = request.data.copy()
        data['owner'] = request.user.pk

        existing_profile = SellerProfile.objects.filter(owner=request.user).first()
        if existing_profile:
            serializer = SellerProfilingDocumentsSerializer(existing_profile, data = data)
        else:
            serializer = SellerProfilingDocumentsSerializer(data = data)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



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



class ProfilingCategoriesView(views.APIView, UserInfoMixin):
    """
    Filling seller operational categories while profiling
    """

    permission_classes = [IsUnapproved]

    def post(self, request, *args, **kwargs):

        sub_categories = request.data['sub_categories']
        profile = request.user.seller_profiles.first()
        profile.operational_fields.set(sub_categories)
        response = self.inject_user_info({'success': True}, request.user)

        return Response(response)
from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, views
from .models import BuyerAddress, BuyerSellerConnection, ManuallyCreatedBuyer, SalespersonProfile, SellerProfile, BuyerProfile
from supplyr.orders.models import Order
from .serializers import BuyerAddressSerializer, BuyerProfileSerializer, SalespersonProfileSerializer2, SellerProfilingSerializer, SellerProfilingDocumentsSerializer, SellerShortDetailsSerializer
from supplyr.core.permissions import IsFromBuyerAPI, IsFromSalesAPI, IsApproved, IsFromSellerAPI, IsUnapproved, IsFromBuyerOrSalesAPI
from supplyr.utils.api.mixins import APISourceMixin
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from supplyr.utils.api.mixins import UserInfoMixin
from django.db import transaction
from collections import OrderedDict

User = get_user_model()

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



class AddressView(generics.ListCreateAPIView, generics.UpdateAPIView, generics.DestroyAPIView, APISourceMixin):
    """
    List, add and edit addresses from buyer app
    """
    # queryset = BuyerAddress.objects.all()
    serializer_class = BuyerAddressSerializer
    permission_classes = [IsFromBuyerOrSalesAPI]
    pagination_class = None

    def get_queryset(self):
        if self.api_source == 'sales':
            profile_id = self.request.GET.get('buyer_id')
        else:
            profile_id = self.request.user.buyer_profiles.first().id
        return BuyerAddress.objects.filter(is_active=True, owner_id = profile_id).order_by('-is_default')

    def perform_create(self, serializer):
        if self.api_source == 'sales':
            owner_id = self.request.GET.get('buyer_id')
        else:
            owner_id = self.request.user.buyer_profiles.first().id
        # owner = self.request.user.buyer_profiles.first()
        serializer.save(owner_id = owner_id)
    
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

class BuyerSearchView(generics.ListAPIView):
    permission_classes = [IsFromSalesAPI]
    serializer_class = BuyerProfileSerializer
    pagination_class = None
    # queryset = SellerProfile.objects.all()
    def get_queryset(self):
        # buyer_profile = self.request.user.get_buyer_profile()
        query = self.request.query_params.get('q')
        return BuyerProfile.objects.filter(
                Q(business_name__istartswith=query) | Q(business_name__icontains= ' ' + query),
                is_active=True
            )

class RecentBuyersView(generics.ListAPIView):
    permission_classes = [IsFromSalesAPI]
    serializer_class = BuyerProfileSerializer
    pagination_class = None
    # queryset = SellerProfile.objects.all()
    def get_queryset(self):
        sales_profile = self.request.user.get_sales_profile()
        # return BuyerProfile.objects.filter(
        #             orders__salesperson_id = sales_profile.id
        #         ).distinct().order_by('-orders__created_at')
        # NOTE: Above query doesn't work and enhanced query like this is only possible in postgresql

        max_recent_shown = 5
        
        buyer_ids_ordered = list(Order.objects.filter(salesperson = 1).order_by('-created_at').values_list('buyer_id', flat=True))  # May contain duplicates
        buyer_ids_ordered = list(OrderedDict.fromkeys(buyer_ids_ordered)) # Duplicates pruned
        buyer_objects = BuyerProfile.objects.filter(pk__in=buyer_ids_ordered) # may be in some other (default) order
        buyer_objects = dict([(obj.id, obj) for obj in buyer_objects])
        buyer_objects_ordered = [buyer_objects[_id] for _id in buyer_ids_ordered[:max_recent_shown]] # ordered by id
        return buyer_objects_ordered

class CreateBuyerView(views.APIView):
    """
    For salesperson, who wishes to add a non existant buyer
    """
    permission_classes = [IsFromSalesAPI]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        business_name = request.data.get('business_name')
        mobile_number = request.data.get('mobile_number')

        errors = {}
        if User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'User already exist with this email ID'
        elif ManuallyCreatedBuyer.objects.filter(email__iexact=email).exists():
            errors['email'] = 'A buyer is already created with this email ID'
        
        if User.objects.filter(mobile_number=mobile_number).exists():
            errors['mobile_number'] = 'User Already exist with this mobile number'
        elif ManuallyCreatedBuyer.objects.filter(mobile_number=mobile_number):
            errors['mobile_number'] = 'A buyer is already created with this mobile number'
        
        if errors:
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)


        buyer_profile = BuyerProfile.objects.create(
            business_name=business_name,
            )
        ManuallyCreatedBuyer.objects.create(
            buyer_profile = buyer_profile,
            email=email,
            mobile_number=mobile_number,
            created_by_id=request.user.get_sales_profile().id
        )

        buyer_profile_data = BuyerProfileSerializer(buyer_profile).data
        return Response(buyer_profile_data)

class SalespersonView(generics.ListCreateAPIView, generics.DestroyAPIView):
    """
    For sellers to list, add or delete salespersons
    """
    serializer_class = SalespersonProfileSerializer2
    permission_classes = [IsFromSellerAPI]
    pagination_class = None

    def get_queryset(self):
        seller_profile = self.request.user.get_seller_profile()
        return SalespersonProfile.objects.filter(seller = seller_profile, is_active = True)

    def post(self, request, *args, **kwargs):
        seller_profile = self.request.user.get_seller_profile()
        salesperson_email = request.data.get('email')
        # salesperson_user = User.objects.filter(email=salesperson_email).first()
        # if not salesperson_user:
        #     return Response({'success': False, 'message': 'User with this email does not exist.'}, status=400)

        # if existing_salesperson := SalespersonProfile.objects.filter(owner=salesperson_user, is_active = True).first():
        #     if existing_salesperson.seller == seller_profile:
        #         message = "This salesperson is already added."
        #     else: 
        #         message = "This salesperson is already added by another seller."
        #     return Response({'success': False, 'message': message}, status=400)

        # else:
        #     seller_profile.salespersons.create(owner=salesperson_user)
        #     return self.get(request, *args, **kwargs)

        if existing_salesperson := (SalespersonProfile.objects.filter(owner__email=salesperson_email, is_active = True).first() or SalespersonProfile.objects.filter(preregistrations__email=salesperson_email, preregistrations__is_settled=False, is_active = True).first()):
            if existing_salesperson.seller == seller_profile:
                message = "This salesperson is already added."
            else: 
                message = "This salesperson is already added by another seller."
            return Response({'success': False, 'message': message}, status=400)

        else:
            # seller_profile.salespersons.create(owner=None)
            salesperson_profile = SalespersonProfile.objects.create(owner=None, seller=seller_profile)
            salesperson_profile.preregistrations.create(email=salesperson_email)

            return self.get(request, *args, **kwargs)


    def delete(self, request, *args, **kwargs):
        seller_profile = self.request.user.get_seller_profile()
        salesperson_id = kwargs.get('pk')

        salesperson_profile = SalespersonProfile.objects.filter(pk=salesperson_id, seller_id=seller_profile.id, is_active = True).first()

        if not salesperson_profile:
            return Response({'success': False, 'message': 'Salesperson is not associated to you.'}, status=400)

        else:
            salesperson_profile.is_active = False
            salesperson_profile.save()
            return self.get(request, *args, **kwargs)



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
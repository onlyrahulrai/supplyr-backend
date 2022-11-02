from django.db.models.query_utils import Q
from django.http.response import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework import generics, mixins, views
from .models import AddressState, BuyerAddress, BuyerSellerConnection, ManuallyCreatedBuyer, SalespersonProfile, SellerProfile, BuyerProfile,SellerAddress,CategoryOverrideGst
from supplyr.orders.models import Order
from .serializers import (
    AddressStatesSerializer, 
    BuyerAddressSerializer, 
    BuyerProfileSerializer, 
    SalespersonProfileSerializer2, 
    SellerProfilingSerializer, 
    SellerProfilingDocumentsSerializer, 
    SellerShortDetailsSerializer,
    SellerAddressSerializer,
    SellerGstConfigSettingSerializer
)
from supplyr.core.permissions import (
    IsFromBuyerAPI,
    IsFromSalesAPI,
    IsApproved, 
    IsFromSellerAPI, 
    IsUnapproved, 
    IsFromBuyerOrSalesAPI,
    IsFromSellerOrSalesAPI,
    IsFromBuyerSellerOrSalesAPI,
    IsFromSellerOrBuyerAPI
)
from supplyr.utils.api.mixins import APISourceMixin

from allauth.account.utils import send_email_confirmation
from allauth.account.admin import EmailAddress
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status
from supplyr.utils.api.mixins import UserInfoMixin
from django.db import transaction
from collections import OrderedDict
from supplyr.core.app_config import TRANSLATABLES
from supplyr.inventory.serializers import *


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

class SellerProfileSettings(views.APIView,UserInfoMixin):
    permission_classes = [IsFromSellerAPI]
    
    def put(self,request,*args,**kwargs):
        data = dict({})
        seller_profile = request.user.seller_profiles.first()
        if request.data.get("setting") == "profile-setting":    
            data = request.data.get("data")
            
            if 'user_settings' in data:
                data = dict({"user_settings":seller_profile.user_settings})
                for key,value in request.data.get("data").get('user_settings',{}).items():
                    data["user_settings"][key] = value  
                    
        elif request.data.get("setting") == "invoice-template-setting":
            data = dict(seller_profile.user_settings)
            
            if "invoice_options" in data:
                data["invoice_options"].update(request.data.get("data",{}))
            
        else:
            data = request.data
            print(" ----- Data ----- ",data)
            
        serializer = SellerProfilingSerializer(seller_profile,data=data,partial=True)
        if serializer.is_valid():
            serializer.save()
            serialized_data = self.inject_user_info({"user_settings":{"translatables":TRANSLATABLES}},request.user)
            return Response(serialized_data,status=status.HTTP_200_OK)
        return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)


class ResendEmailConfirmation(views.APIView):
    permission_classes = [IsAuthenticated] 

    def post(self, request, *args, **kwargs):
        user = request.user
        print('userrr ', user.email)
        is_already_verified = EmailAddress.objects.filter(user=user, verified=True).exists()

        if is_already_verified:
            return Response({'message': 'This email is already verified'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            try:
                send_email_confirmation(request, user=user)
                return Response({'message': 'Email confirmation sent'}, status=status.HTTP_201_CREATED)
            except:
                return Response({'message': 'An unexpected error occurred'}, status=status.HTTP_403_FORBIDDEN)


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
    # permission_classes = [IsFromBuyerOrSalesAPI]
    permission_classes = [IsFromBuyerSellerOrSalesAPI]
    pagination_class = None

    def get_queryset(self):
        if self.api_source == 'sales' or self.api_source == "seller":
            profile_id = self.request.GET.get('buyer_id')
        else:
            profile_id = self.request.user.buyer_profiles.first().id
        return BuyerAddress.objects.filter(is_active=True, owner_id = profile_id).order_by('-is_default')

    def list(self, request, *args, **kwargs):
        # To retuen 'states_list' as well along with 'addresses'
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset, many=True)
        addresses_list = serializer.data


        states_list = AddressStatesSerializer(AddressState.objects.all(), many=True).data
        rsp = {
            'addresses': addresses_list,
            'states_list': states_list
        }

        # address_state_values = 
        return Response(rsp)

    def perform_create(self, serializer):
        if self.api_source == 'sales' or self.api_source == 'seller':
            owner_id = self.request.GET.get('buyer_id')
        else:
            owner_id = self.request.user.buyer_profiles.first().id
        # owner = self.request.user.buyer_profiles.first()
        serializer.save(owner_id = owner_id)
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save()

class SellerAddressView(generics.ListCreateAPIView,generics.UpdateAPIView,APISourceMixin):
    pagination_class = None
    serializer_class = SellerAddressSerializer
    permission_classes = [IsApproved]
    
    def get_queryset(self):
        owner = self.request.user.seller_profiles.first().id
        return SellerAddress.objects.filter(owner=owner,is_active=True).order_by('-is_default')
    
    def perform_create(self, serializer):
        owner = self.request.user.seller_profiles.first().id
        serializer.save(owner_id=owner,is_default=True)
        
    def post(self,request,*args,**kwargs):        
        if id := kwargs.get("pk"):
            return self.update(request, *args, **kwargs)
        return self.create(request, *args, **kwargs)
    
    def get(self, request,*args,**kwargs):
        queryset = self.get_queryset()
        serializer = self.serializer_class(queryset,many=True)
        
        states_list = AddressStatesSerializer(AddressState.objects.all(), many=True).data
        rsp = {
            'addresses': serializer.data,
            'states_list': states_list
        }
        
        return Response(rsp)
        
class SellerView(views.APIView, APISourceMixin):

    permission_classes = [IsAuthenticated, IsFromSellerOrBuyerAPI]

    def post(self, request, *args, **kwargs):
        code = request.data['buyer_id'] if "seller" in request.resolver_match.kwargs.values() else request.data['connection_code']
        
        if "seller" in request.resolver_match.kwargs.values():
            seller = request.user.get_seller_profile()
            buyer = get_object_or_404(BuyerProfile,id=code)
            connection,created = BuyerSellerConnection.objects.get_or_create(seller=seller, buyer = buyer)
            return Response(SellerBuyersConnectionSerializer(buyer).data)
        else:
            if seller := SellerProfile.objects.filter(connection_code__iexact = code, is_active= True, status=SellerProfile.SellerStatusChoice.APPROVED).first():
                connection,created = BuyerSellerConnection.objects.get_or_create(seller=seller, is_active=True, buyer = self.request.user.get_buyer_profile())
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
    permission_classes = [IsFromSellerOrSalesAPI]
    serializer_class = BuyerProfileSerializer
    pagination_class = None
    # queryset = SellerProfile.objects.all()
    def get_queryset(self):
        # buyer_profile = self.request.user.get_buyer_profile()
        query = self.request.query_params.get('q')
        
        # return BuyerProfile.objects.filter(
        #         Q(business_name__istartswith=query) | Q(business_name__icontains= ' ' + query),
        #         is_active=True
        #     )
        
        return BuyerProfile.objects.filter(Q(business_name__icontains=query) | Q(owner__email__icontains=query) | Q(owner__mobile_number__icontains=query) | Q(manuallycreatedbuyer__email__icontains=query) | Q(manuallycreatedbuyer__mobile_number__icontains=query)).prefetch_related('manuallycreatedbuyer_set')

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
        
        buyer_ids_ordered = list(Order.objects.filter(salesperson = sales_profile).order_by('-created_at').values_list('buyer_id', flat=True))  # May contain duplicates
        buyer_ids_ordered = list(OrderedDict.fromkeys(buyer_ids_ordered)) # Duplicates pruned
        buyer_objects = BuyerProfile.objects.filter(pk__in=buyer_ids_ordered) # may be in some other (default) order
        buyer_objects = dict([(obj.id, obj) for obj in buyer_objects])
        buyer_objects_ordered = [buyer_objects[_id] for _id in buyer_ids_ordered[:max_recent_shown]] # ordered by id
        return buyer_objects_ordered

class CreateBuyerView(views.APIView):
    """
    For salesperson, who wishes to add a non existant buyer
    """
    # permission_classes = [IsFromSalesAPI]
    permission_classes = [IsFromSellerOrSalesAPI]

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
        profile = request.user.get_seller_profile() if "seller" in request.resolver_match.kwargs.values() else request.user.get_sales_profile()
        

        if "seller" in request.resolver_match.kwargs.values():
            connection,created = BuyerSellerConnection.objects.get_or_create(buyer=buyer_profile,seller=profile)
            ManuallyCreatedBuyer.objects.create(
                buyer_profile = buyer_profile,
                email=email,
                mobile_number=mobile_number,
                created_by_seller=profile
            )
        else:
            ManuallyCreatedBuyer.objects.create(
                buyer_profile = buyer_profile,
                email=email,
                mobile_number=mobile_number,
                created_by=profile
            )

        # buyer_profile_data = BuyerProfileSerializer(buyer_profile).data
        buyer_profile_data = SellerBuyersConnectionSerializer(buyer_profile).data
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

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):

        sub_categories = request.data['sub_categories']
        profile = request.user.seller_profiles.first()
        profile.operational_fields.set(sub_categories)
        
        
        if not request.user.is_approved:
            if(profile.status == "new"):
                profile.status = "categories_selected"
                profile.save()
        
        response = self.inject_user_info({'success': True}, request.user)

        return Response(response)
    
class ApplyForApproval(views.APIView,UserInfoMixin):
    '''
        It's allow user to make request to the reviewer for thier account approval. 
    '''
    permission_classes = [IsUnapproved]
    def post(self,request,*args,**kwargs):
        seller_profile = request.user.seller_profiles.first()
        seller_profile.status = "pending_approval"
        seller_profile.save()
        response = self.inject_user_info({'success': True}, request.user)
        return Response(response)
    
class GstConfigSettingAPIView(generics.CreateAPIView,generics.RetrieveAPIView):
    permission_classes = [IsApproved]
    serializer_class = SellerGstConfigSettingSerializer
    queryset = SellerProfile.objects.filter(is_active=True)
    
    def get(self,request,*args,**kwargs):
        seller = request.user.seller_profiles.first()
        serializer = self.serializer_class(seller)
        return Response(serializer.data)
    
    def post(self,request,*args,**kwargs):
        with transaction.atomic():
            data = request.data
            seller = request.user.seller_profiles.first()
            override_categories = data.pop('override_categories',[])
            
            initial_override_categories = seller.override_categories.filter(is_active=True).values_list("id",flat=True)
            
            override_categories_ids = []
            
            for override_category in override_categories:
                categoryID = override_category.pop("category")
                
                categoryInstance = get_object_or_404(Category,id=categoryID)
                
                if override_category.get("id"):
                    category_override_gst = CategoryOverrideGst(category=categoryInstance,seller=seller,**override_category)
                else:
                    category_override_gst = CategoryOverrideGst.objects.create(category=categoryInstance,seller=seller,**override_category)
                
                category_override_gst.save()
                
                override_categories_ids.append(category_override_gst.id)
                
            override_category_to_remove = [_override_category for _override_category in initial_override_categories if  _override_category not in override_categories_ids]
            
            
            CategoryOverrideGst.objects.filter(id__in=override_category_to_remove).update(is_active=False)    
                    
            serializer = self.serializer_class(seller,data=data,partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors)
    
    
    
    
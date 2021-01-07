from rest_framework import serializers
from .models import BuyerAddress, BuyerProfile, SellerProfile, SalespersonProfile
from django.contrib.auth import get_user_model
from typing import Dict
from supplyr.inventory.models import Category, SubCategory
from supplyr.inventory.serializers import SubCategorySerializer2, SubCategorySerializer


User = get_user_model()

class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]

    # def to_internal_value(self, data):
    #     # To support inserts with the value
    #     if data == '' and self.allow_blank:
    #         return ''

    #     for key, val in self._choices.items():
    #         if val == data:
    #             return key
    #     self.fail('invalid_choice', input=data)


class ShortEntityDetailsSerializer(serializers.ModelSerializer):
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, profile):
        sub_categories = profile.operational_fields.all()
        sub_categories_serializer = SubCategorySerializer2(sub_categories, many=True)
        return sub_categories_serializer.data

    class Meta:
        model = SellerProfile
        fields = [
            'business_name',
            'id',
            'sub_categories',
            'connection_code',
            ]



class CategoriesSerializer(serializers.ModelSerializer):
    """
    Used for generating cateogries list for displaying in seller profiling form
    """
    
    sub_categories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        fields = [
            'name',
            'id',
            'sub_categories'
        ]
        depth = 1

def _get_seller_profiling_data(user: User) -> Dict:

    existing_profile = user.seller_profiles.first()
    entity_details = None
    user_selected_sub_categories = []
    if  existing_profile:
        entity_details = SellerProfilingSerializer(existing_profile).data
        user_selected_sub_categories = existing_profile.operational_fields.all().values_list('id', flat=True)

    ### Category Information
    categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
    cat_serializer = CategoriesSerializer(categories, many=True)
    cat_serializer_data = cat_serializer.data

    categories_data = {
            'categories': cat_serializer_data,
            'selected_sub_categories': user_selected_sub_categories
        }

    profiling_data = {
        'entity_details': entity_details,
        'categories_data': categories_data
    }
    
    return profiling_data

class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = [
            'id', 
            'business_name',
            'owner',
        ]
        extra_kwargs = {
            'owner': {
                'write_only': True
            }
        }


class UserDetailsSerializer(serializers.ModelSerializer):
    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None

    profiling_data = serializers.SerializerMethodField()
    def get_profiling_data(self, user):
        """
        Profiling data for people who are still filling the profiling form
        """
        if not user.is_approved:
            return _get_seller_profiling_data(user) 
        return None
    
    profile = serializers.SerializerMethodField()
    def get_profile(self, user):
        """
        Profile details for people who are approved
        """

        if self._get_api_source() == 'buyer':
            if profile := user.buyer_profiles.first():
                return BuyerProfileSerializer(profile).data

        elif self._get_api_source() == 'sales':
            if profile := user.salesperson_profiles.first():
                return SalespersonProfileSerializer(profile).data

        elif user.is_approved: # seller profile
            profile = user.seller_profiles.first()
            return ShortEntityDetailsSerializer(profile).data
            
        return None

    user_status = serializers.SerializerMethodField()
    def get_user_status(self, user):
        if self._get_api_source() == 'buyer':
            return user.buyer_status
        elif self._get_api_source() == 'seller':
            return user.seller_status
        elif self._get_api_source() == 'sales':
            return user.salesperson_status
        
        return None


    user_role = serializers.SerializerMethodField()
    def get_user_role(self, user):
        if user.is_superuser:
            return "admin"
        elif user.is_staff:
            return "staff"
        return None

    class Meta:
        model = User
        fields = ['name', 'first_name', 'last_name', 'username', 'is_staff', 'user_status', 'profiling_data', 'profile', 'user_role', 'is_email_verified', 'is_mobile_verified', 'email', 'mobile_number']


class BuyerAddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerAddress
        # fields = '__all__'
        exclude = ['owner']

    state = ChoiceField(choices=BuyerAddress.STATE_CHOICES)


class SellerProfilingSerializer(serializers.ModelSerializer):

    # def validate(self, data):
    #     if data['gst_number'] == '123':
    #         raise serializers.ValidationError("Dummy Error")  
    #     return data

    class Meta:
        model = SellerProfile
        fields = [
            'owner',
            'business_name',
            'entity_category',
            'entity_type',
            'is_gst_enrolled',
            'gst_number',
            'pan_number',
            'tan_number',
            'gst_certificate',
            ]

        read_only_fields = [
            'gst_certificate',
            ]

        extra_kwargs = {
            'business_name': {
                'required': True,
                'allow_null': False,
                'allow_blank': False
            },
            'entity_category': {
                'required': True,
                'allow_null': False,
            },
            'entity_type': {
                'required': True,
                'allow_null': False,
                'allow_blank': False
            },
        }

class SellerProfilingDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = [
            'owner',
            'gst_certificate'
            ]


class SellerShortDetailsSerializer(serializers.ModelSerializer):

    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, profile):
        sub_categories = profile.operational_fields.filter(products__owner = profile, products__is_active=True).distinct()
        sub_categories_serializer = SubCategorySerializer2(sub_categories, many=True)
        return sub_categories_serializer.data

    has_products_added = serializers.SerializerMethodField()
    def get_has_products_added(self, seller):
        return seller.products.filter(is_active=True).exists()

    class Meta:
        model = SellerProfile
        fields = [
            'business_name',
            'sub_categories',
            'id',
            'has_products_added',
            ]


class SalespersonProfileSerializer(serializers.ModelSerializer):
    """
    To be used in fetching user details in case of request from salesperson api.
    """

    seller = SellerShortDetailsSerializer()

    class Meta:
        model = SalespersonProfile
        fields = [
            'id',
            'seller'
            ]

class SalespersonProfileSerializer2(serializers.ModelSerializer):
    """
    To be used in fetching salespersons list in case of request from  seller api
    """

    name = serializers.CharField(source='owner.name')
    email = serializers.CharField(source='owner.email')

    class Meta:
        model = SalespersonProfile
        fields = [
            'id',
            'name',
            'email'
            ]

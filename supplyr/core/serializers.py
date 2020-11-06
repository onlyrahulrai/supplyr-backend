from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer
from .models import SellerProfile, Category, SubCategory, BuyerProfile
from typing import Dict
import json
import re
from rest_framework.exceptions import ValidationError


User = get_user_model()

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

        elif user.is_approved: # seller profile
            profile = user.seller_profiles.first()
            return ShortEntityDetailsSerializer(profile).data
            
        return None

    seller_status = serializers.SerializerMethodField()
    def get_seller_status(self, user):
        if self._get_api_source() == 'buyer':
            return None
        return user.seller_status

    buyer_status = serializers.SerializerMethodField()
    def get_buyer_status(self, user):
        if self._get_api_source() == 'seller':
            return None
        return user.buyer_status

    class Meta:
        model = User
        fields = ['name', 'first_name', 'last_name', 'username', 'is_staff', 'seller_status', 'buyer_status', 'profiling_data', 'profile']


class CustomRegisterSerializer(RegisterSerializer):
    
    def save(self, request):
        
        first_name = request.data['first_name'].strip()
        last_name = request.data['last_name'].strip()
        mobile_number = request.data['mobile_number'].strip()

        if not first_name:
            raise ValidationError({'first_name': 'First name is required'})

        mobile_pattern = re.compile("(0|91|\+91)?[6-9][0-9]{9}$") 
        if not mobile_pattern.match(mobile_number):
            raise ValidationError({'mobile_number': 'Please enter a valid mobile number'})

        

        user = super().save(request)

        user.first_name = first_name
        user.last_name = last_name
        user.mobile_number = mobile_number
        user.save()
        return user

class CustomJWTSerializer(JWTSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['user_info'] = ret['user']
        del ret['user']
        return ret

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

class SubCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = SubCategory
        fields = [
            'id',
            'name'
        ]

class SubCategorySerializer2(serializers.ModelSerializer):
    category = serializers.CharField(source='category.name')
    
    class Meta:
        model = SubCategory
        fields = [
            'id',
            'name',
            'category'
        ]

class CategoriesSerializer(serializers.ModelSerializer):
    
    sub_categories = SubCategorySerializer(many=True)

    class Meta:
        model = Category
        fields = [
            'name',
            'id',
            'sub_categories'
        ]
        depth = 1

class CategoriesSerializer2(serializers.ModelSerializer):
    
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, category):
        sub_categories = category.sub_categories.filter(is_active =True)
        return SubCategorySerializer(sub_categories, many=True).data

    class Meta:
        model = Category
        fields = [
            'name',
            'id',
            'sub_categories',
            'image'
        ]
        extra_kwargs = {
            'image': {
                'required': False,
            },
        }
        # depth = 1

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        sub_categories_raw_data = json.loads(data['sub_categories'])
        sub_categories_data = map(lambda sc: {_key: sc[_key] for _key in ['name', 'id'] if _key in sc}, sub_categories_raw_data) # By default, 'id' field for sub categories was omitted., hence needed to include it
        value['sub_categories'] = sub_categories_data # By default,  'id' field for sub categories was omitted.
        if 'delete_image' in data:
            value['delete_image'] = data['delete_image']
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image_sm.url
        return representation

    def create(self, validated_data):
        # Not very secure, for staff use only. Will need to add more security if it needs to be open to public, like popping ID field
        sub_categories_data = validated_data.pop('sub_categories')
        category = Category.objects.create(**validated_data)
        for sub_category in sub_categories_data:
            SubCategory.objects.create(category=category, **sub_category)

        return category

    def update(self, instance, validated_data):
        instance.name = validated_data['name']
        if 'delete_image' in validated_data:
            instance.image.delete(save=False)
        elif 'image' in validated_data:
            instance.image = validated_data['image']
        instance.save()

        sub_categories_initial = list(instance.sub_categories.values_list('id', flat=True))
        sub_categories_final = []
        sub_categories_data = validated_data.pop('sub_categories')
        for sc_data in sub_categories_data:
            sc = SubCategory(category_id=instance.id, **sc_data)
            sc.save()
            sub_categories_final.append(sc.id)
            
        sub_categories_to_remove = [sc for sc in sub_categories_initial if sc not in sub_categories_final]
        SubCategory.objects.filter(id__in=sub_categories_to_remove).update(is_active = False)
        return instance

        
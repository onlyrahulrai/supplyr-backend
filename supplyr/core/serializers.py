from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer
from .models import Profile, Category, SubCategory


User = get_user_model()

def get_profiling_data(user):
    existing_profile = user.profiles.first()
    if not existing_profile:
        return None
    details_serializer = ProfilingSerializer(existing_profile)
    entity_details = details_serializer.data

    ### Category Information
    categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
    cat_serializer = CategoriesSerializer(categories, many=True)
    cat_serializer_data = cat_serializer.data

    user_selected_sub_categories = user.profiles.first().operational_fields.all().values_list('id', flat=True)

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
    profiling_data = serializers.SerializerMethodField()

    def get_profiling_data(self, user):
        if user.status != 'approved':
            return get_profiling_data(user) 
        return None

    class Meta:
        model = User
        fields = ['name', 'username', 'is_staff', 'status', 'profiling_data']


class CustomRegisterSerializer(RegisterSerializer):
    
    def save(self, request):
        name = request.data['name']

        user = super().save(request)
        user.first_name = name
        user.save()
        return user

class CustomJWTSerializer(JWTSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['user_info'] = ret['user']
        del ret['user']
        return ret


class ProfilingSerializer(serializers.ModelSerializer):

    # def validate(self, data):
    #     if data['gst_number'] == '123':
    #         raise serializers.ValidationError("Dummy Error")  
    #     return data

    class Meta:
        model = Profile
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

class ProfilingDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
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
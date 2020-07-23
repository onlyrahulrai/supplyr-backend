from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Profile

User = get_user_model()

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'username', 'is_staff', 'status']


class CustomRegisterSerializer(RegisterSerializer):
    
    def save(self, request):
        name = request.data['name']

        user = super().save(request)
        user.first_name = name
        user.save()
        return user


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

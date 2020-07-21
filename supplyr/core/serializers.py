from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from .models import Entity

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
    class Meta:
        model = Entity
        fields = [
            'owner',
            'business_name',
            'entity_category',
            'entity_type',
            'is_gst_enrolled',
            'gst_number',
            'pan_number',
            'tan_number'
            ]

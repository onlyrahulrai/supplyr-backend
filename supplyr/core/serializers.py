from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer

User = get_user_model()

class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'username', 'is_staff', 'state']


class CustomRegisterSerializer(RegisterSerializer):
    
    def save(self, request):
        name = request.data['name']

        user = super().save(request)
        user.first_name = name
        user.save()
        return user
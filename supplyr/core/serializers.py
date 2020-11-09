from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer
# from .models import SellerProfile, Category, SubCategory, BuyerProfile
from supplyr.profiles.models import SellerProfile, BuyerProfile
from supplyr.inventory.models import Category, SubCategory
import json
import re
from rest_framework.exceptions import ValidationError


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

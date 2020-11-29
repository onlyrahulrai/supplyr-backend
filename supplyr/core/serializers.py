from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer
# from .models import SellerProfile, Category, SubCategory, BuyerProfile
from supplyr.profiles.models import SellerProfile, BuyerProfile
from supplyr.inventory.models import Category, SubCategory
import json
import re
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from supplyr.profiles.models import ManuallyCreatedBuyer


class CustomRegisterSerializer(RegisterSerializer):

    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None
    
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

        if self._get_api_source() == 'buyer':
            if manual_buyer := ManuallyCreatedBuyer.objects.filter(Q(mobile_number=mobile_number) | Q(email=user.email)).first():
                manual_buyer.buyer_profile.owner = user
                manual_buyer.buyer_profile.save()
                manual_buyer.is_settled = True
                manual_buyer.save()


        return user

class CustomJWTSerializer(JWTSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['user_info'] = ret['user']
        del ret['user']
        return ret

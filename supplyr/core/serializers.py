from django.contrib.auth import get_user_model
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer, LoginSerializer
# from .models import SellerProfile, Category, SubCategory, BuyerProfile
from supplyr.profiles.models import SalespersonPreregisteredUser, SellerProfile, BuyerProfile
from supplyr.inventory.models import Category, SubCategory
import json
from supplyr.utils.general import validate_mobile_number
from django.db.models import Q
from rest_framework.exceptions import ValidationError
from supplyr.profiles.models import ManuallyCreatedBuyer


User = get_user_model()


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
        email = request.data['email'].strip()

        if not first_name:
            raise ValidationError({'first_name': 'First name is required'})

        if not validate_mobile_number(mobile_number):
            raise ValidationError({'mobile_number': 'Please enter a valid mobile number'})

        if self._get_api_source() == 'sales':
            if not SalespersonPreregisteredUser.objects.filter(email = email).exists():
                raise ValidationError({'email': 'This email is not linked to any seller yet'})

        

        user = super().save(request)

        user.first_name = first_name
        user.last_name = last_name
        user.mobile_number = mobile_number
        user.save()

        # if self._get_api_source() == 'buyer':
        #     if manual_buyer := ManuallyCreatedBuyer.objects.filter(Q(mobile_number=mobile_number) | Q(email=user.email)).first():
        #         manual_buyer.buyer_profile.owner = user
        #         manual_buyer.buyer_profile.save()
        #         manual_buyer.is_settled = True
        #         manual_buyer.save()

        if self._get_api_source() == 'sales':
            preregistered_user = SalespersonPreregisteredUser.objects.filter(email = email).first()
            preregistered_user.salesperson_profile.owner = user
            preregistered_user.salesperson_profile.save()
            preregistered_user.is_settled = True
            preregistered_user.save()


        return user


class CustomLoginSerializer(LoginSerializer):
    
    email = serializers.CharField(required=False, allow_blank=True)

    def get_auth_user_using_allauth(self, username, email, password):
        """
        If user has entered mobile number as username, convert that to corresponding email address to make it compatible with authentication backend
        """
        _email = email.strip()
        if _email.isdigit():
            if user := User.objects.filter(mobile_number = _email).first():
                _email = user.email
        return super().get_auth_user_using_allauth(username, _email, password)
        

class CustomJWTSerializer(JWTSerializer):
    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['user_info'] = ret['user']
        del ret['user']
        return ret

from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework import serializers
from dj_rest_auth.registration.serializers import RegisterSerializer
from dj_rest_auth.serializers import JWTSerializer, LoginSerializer, PasswordResetSerializer
from supplyr.profiles.models import SalespersonPreregisteredUser
from supplyr.utils.general import validate_mobile_number
from rest_framework.exceptions import ValidationError
from django.contrib.auth.forms import SetPasswordForm
# if 'allauth' in settings.INSTALLED_APPS:
# from allauth.account.forms import default_token_generator
# from allauth.account.utils import url_str_to_user_pk as uid_decoder
    
# else:
from django.contrib.auth.tokens import default_token_generator 
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.utils.encoding import force_text
from supplyr.core.functions import ManuallyCreatedBuyer
from django.db.models import Q


User = get_user_model()


class CustomRegisterSerializer(RegisterSerializer):

    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                print(kwargs)
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
            raise ValidationError({'mobile_number': 'Please enter a valid 10-digit mobile number'})

        if self._get_api_source() == 'sales':
            if not SalespersonPreregisteredUser.objects.filter(email = email).exists():
                raise ValidationError({'email': 'This email is not linked to any seller yet'})

        

        user = super().save(request)
        
        print(self._get_api_source())

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

        if self._get_api_source() == 'sales':
            preregistered_user = SalespersonPreregisteredUser.objects.filter(email = email).first()
            preregistered_user.salesperson_profile.owner = user
            preregistered_user.salesperson_profile.save()
            preregistered_user.is_settled = True
            preregistered_user.save()


        return user

class CustomPasswordResetSerializer(PasswordResetSerializer):
    def get_email_options(self):

        print("selff ", vars(self))

        password_reset_url_base = settings.URL_FRONTEND + 'forgot-password/'

        """Override this method to change default e-mail options"""
        return {
            'html_email_template_name':'registration/password_reset_email.html',
            'extra_email_context': {
                'password_reset_url_base': password_reset_url_base
            }
        }
        
class PasswordResetConfirmSerializer(serializers.Serializer):
        """
        Serializer for requesting a password reset e-mail.
        """
        new_password1 = serializers.CharField(max_length=128)
        new_password2 = serializers.CharField(max_length=128)
        uid = serializers.CharField()
        token = serializers.CharField()

        set_password_form_class = SetPasswordForm

        def custom_validation(self, attrs):
            print(vars(attrs))
            pass

        def validate(self, attrs):
                self._errors = {}

                # Decode the uidb64 to uid to get User object
                try:
                    uid = force_text(uid_decoder(attrs['uid']))
                    print(uid)
                    self.user = User._default_manager.get(pk=uid)
                except (TypeError, ValueError, OverflowError, User.DoesNotExist):
                        raise ValidationError({'uid': ['Invalid value']})

                self.custom_validation(attrs)
                # Construct SetPasswordForm instance
                self.set_password_form = self.set_password_form_class(
                        user=self.user, data=attrs
                )
                if not self.set_password_form.is_valid():
                        raise serializers.ValidationError(self.set_password_form.errors)
                if not default_token_generator.check_token(self.user, attrs['token']):
                        raise ValidationError({'token': ['Invalid value']})

                print(attrs)
                return attrs
        def save(self):
            return self.set_password_form.save()
            
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

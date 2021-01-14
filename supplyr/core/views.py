from supplyr.core.functions import check_and_link_manually_created_buyer
from supplyr.orders.models import Order
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import mixins, generics

from dj_rest_auth.views import LoginView

from .permissions import IsFromSellerAPI, IsUnapproved, IsFromBuyerAPI
from supplyr.profiles.models import BuyerSellerConnection, SellerProfile, BuyerProfile
from supplyr.inventory.models import Category, Product

from supplyr.utils.api.mixins import APISourceMixin
from supplyr.utils.api.mixins import UserInfoMixin
from supplyr.utils.general import validate_mobile_number

User = get_user_model()


class UserDetailsView(APIView, UserInfoMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        response_data = self.inject_user_info({}, user)

        return Response(response_data)


class CustomLoginView(LoginView, APISourceMixin):
    def get_response(self):
        response = super().get_response()
        print("SRC ", self.request.user)
        # response.data['user_info'] = response.data['user']
        # del response.data['user']
        # response.set_cookie('refresh', self.refresh_token)
        return response

class SellerDashboardStats(APIView):
    permission_classes = [IsFromSellerAPI]
    def get(self, request, *args, **kwargs):
        seller_profile = request.user.get_seller_profile()

        response = {}
        _order_status_counts = Order.objects.filter(seller_id=seller_profile.id, is_active = True).values('status').annotate(count=Count('created_at')).order_by()
        order_status_counts = {}
        for status_count in _order_status_counts:
            order_status_counts[status_count['status']] = status_count['count']
        
        for status in Order.OrderStatusChoice.choices:  # Including those status whose count may be zero, hence not returned by db query
            if not status[0] in order_status_counts:
                order_status_counts[status[0]] = 0


        date_today = timezone.localtime().date()
        date_before_7_days = date_today - timezone.timedelta(days=7)

        last_week_orders = Order.objects.filter(seller_id=seller_profile.id, created_at__gt=date_before_7_days).values('created_at__date').annotate(count=Count('id'), amount=Sum('total_amount')).order_by()
        weekly_stats = []

        for week_index in range(0, 7):
            date = date_before_7_days + timezone.timedelta(days=week_index)
            weekday_data = list(
                filter(
                    lambda x: x['created_at__date']== date,
                    list(last_week_orders)
                )
            )
            if not weekday_data:
                weekday_data = {
                    'count': 0,
                    'amount': 0
                }
            else:
                weekday_data = weekday_data[0]
            
            weekly_stats.append({
                'date': date.strftime('%b %d'),
                'count': weekday_data['count'],
                'amount': weekday_data['amount']
            })

        today_data = list(filter(
                    lambda x: x['created_at__date'] == date_today,
                    list(last_week_orders)
                ))

        daily_stats = {
            'count': today_data[0]['count'],
            'amount': today_data[0]['amount']
        }   if today_data else {
            'count': 0,
            'amount': 0
        }

        
        products_count = Product.objects.filter(owner_id = seller_profile.id).count()
        buyers_count = BuyerSellerConnection.objects.filter(is_active = True, seller_id=seller_profile.id).count()

        response = {
            'daily_order_stats': daily_stats,
            'weekly_order_stats': weekly_stats,
            'order_status_counts': order_status_counts,
            'products_count': products_count,
            'buyers_count': buyers_count,

        }


        return Response(response)


def generate_and_send_mobile_verification_otp(user):
    error_message = None

    if user.is_mobile_verified:
        error_message = "User's number already verified"

    otp = user.verification_otps.filter(mobile_number = user.mobile_number, created_at__gt = timezone.now() - timedelta(minutes=settings.MOBILE_VERIFICATION_OTP_EXPIRY_MINUTES -1 )).first()
    if not otp:
        otp = user.verification_otps.create(mobile_number = user.mobile_number)
    
    res = otp.send()
    if res:
        return Response({
            'success': True,
            'otp_id': otp.id
        })
    else:
        error_message = "Unknown Error"
    
    if error_message:
        return Response({
            'success': False, 'message': error_message
        })
    
    


class SendMobileVerificationOTP(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        return generate_and_send_mobile_verification_otp(request.user)

class VerifyMobileVerificationOTP(APIView, UserInfoMixin):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        code = request.data.get('code')
        otp_id = request.data.get('otp_id')
        user = request.user

        if otp := user.verification_otps.filter(mobile_number = user.mobile_number, code=code, id=otp_id, created_at__gt = timezone.now() - timedelta(minutes=settings.MOBILE_VERIFICATION_OTP_EXPIRY_MINUTES)).first():
            user.is_mobile_verified = True
            user.save()


            try:
                if user.is_credentials_verified:
                    check_and_link_manually_created_buyer(user)
            except Exception as e:
                print(e)
                #TODO: raise exception

            response_data = self.inject_user_info({'success': True}, user)
            return Response(response_data)
        
        else:
            return Response({
                'success': False, 'message': 'Invalid or expired OTP'
            })

class ChangeEmailView(APIView, UserInfoMixin):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        new_email = request.data.get('new_email')
        if user.is_email_verified:
            return Response({'success': False, 'message': "Email is verified, can't change"}, status=400)

        if User.objects.exclude(id=user.id).filter(email = new_email).exists():
            return Response({
                'success': False, 'message': 'Email already added by some other user'
            }, status=400)
        
        if email := user.emailaddress_set.filter(email = user.email).first():
            try: 
                email.change(request, new_email)
                return Response(self.inject_user_info({
                    'success': True
                }, user))
            except Exception as e:
                return Response({
                    'success': False, 'message': str(e)
                }, status=500)

class ChangeMobileNumberView(APIView, UserInfoMixin):

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        new_mobile = request.data.get('new_mobile')

        if not validate_mobile_number(new_mobile):
            return Response({'success': False, 'message': 'Please enter a valid 10-digit mobile number'}, status=400)

        if user.is_mobile_verified:
            return Response({'success': False, 'message': "Mobile number is verified, can't change"}, status=400)

        if User.objects.exclude(id=user.id).filter(mobile_number = new_mobile).exists():
            return Response({
                'success': False, 'message': 'Mobile Number already added by some other user'
            }, status=400)
        
        
        user.mobile_number = new_mobile
        user.save()
        return Response(self.inject_user_info({
            'success': True
        }, user))

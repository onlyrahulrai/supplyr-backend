from supplyr.orders.models import Order
from django.shortcuts import render
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum
from django.utils import timezone
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

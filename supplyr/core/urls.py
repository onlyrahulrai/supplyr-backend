
from django.contrib import admin
from django.urls import path, include
from django.urls.conf import re_path
from django.views.generic.base import TemplateView
from rest_framework import routers
# from rest_framework_simplejwt.views import TokenRefreshView
# from rest_framework.authtoken.views import obtain_auth_token

from supplyr.core.views import SellerDashboardStats, UserDetailsView, CustomLoginView, SendMobileVerificationOTP, VerifyMobileVerificationOTP, ChangeEmailView, ChangeMobileNumberView

# router = routers.DefaultRouter()
# router.register(r'users', UserDetailsViewSet)

urlpatterns = [
    # path('', include(router.urls)),
    path('login/', CustomLoginView.as_view()),
    path('register/', include('dj_rest_auth.registration.urls')),
    path('send-mobile-verification-otp/', SendMobileVerificationOTP.as_view(), name='send-mobile-verification-otp'),
    path('verify-mobile-verification-otp/', VerifyMobileVerificationOTP.as_view(), name='verify-mobile-verification-otp'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('change-mobile/', ChangeMobileNumberView.as_view(), name='change-mobile'),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('dj_rest_auth.urls')),
    path('user-details/', UserDetailsView.as_view()),
    path('seller-dashboard-stats/', SellerDashboardStats.as_view(), name='seller_dashboard_stats')
]


from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
# from rest_framework_simplejwt.views import TokenRefreshView
# from rest_framework.authtoken.views import obtain_auth_token

from supplyr.core.views import SellerDashboardStats, UserDetailsView, CustomLoginView, SendMobileVerificationOTP, VerifyMobileVerificationOTP

# router = routers.DefaultRouter()
# router.register(r'users', UserDetailsViewSet)

urlpatterns = [
    # path('', include(router.urls)),
    path('login/', CustomLoginView.as_view()),
    path('register/', include('dj_rest_auth.registration.urls')),
    path('send-mobile-verification-otp/', SendMobileVerificationOTP.as_view(), name='send-mobile-verification-otp'),
    path('verify-mobile-verification-otp/', VerifyMobileVerificationOTP.as_view(), name='verify-mobile-verification-otp'),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('user-details/', UserDetailsView.as_view()),
    path('seller-dashboard-stats/', SellerDashboardStats.as_view(), name='seller_dashboard_stats')
]

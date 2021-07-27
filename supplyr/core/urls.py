
from django.contrib import admin
from django.urls import path, include
from django.urls.conf import re_path
from django.views.generic.base import TemplateView
from rest_framework import routers
# from rest_framework_simplejwt.views import TokenRefreshView
# from rest_framework.authtoken.views import obtain_auth_token

from supplyr.core.views import SellerDashboardStats, UpdateMobileNumberConfirmView, UpdateMobileNumberView, UserDetailsView, CustomLoginView, SendMobileVerificationOTP, VerifyMobileVerificationOTP, ChangeEmailView, ChangeMobileNumberView,RequestForgetPassword,PasswordResetEmailConfirmView, PasswordResetMobileConfirmView
# ForgetPasswordConfirm




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
    path('update-mobile/', UpdateMobileNumberView.as_view(), name='update-mobile'),
    path('confirm-update-mobile/', UpdateMobileNumberConfirmView.as_view(), name='confirm-update-mobile'),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/', include('dj_rest_auth.urls')),
    path('user-details/', UserDetailsView.as_view()),
    path('seller-dashboard-stats/', SellerDashboardStats.as_view(), name='seller_dashboard_stats'),
    path("request-forget-password/",RequestForgetPassword.as_view(),name="request-forget-password"),
    # path("request-forget-password-confirm/",ForgetPasswordConfirm.as_view(),name="forget-password-confirm"),
    path('password-reset-email-confirm/', PasswordResetEmailConfirmView.as_view(),
        name='password-reset-email-confirm'),
    path('password-reset-mobile-confirm/', PasswordResetMobileConfirmView.as_view(),
        name='password-reset-mobile-confirm'),
]

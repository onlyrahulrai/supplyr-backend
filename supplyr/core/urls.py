from django.urls import path, include
from supplyr.core.views import *

urlpatterns = [
    path('login/', CustomLoginView.as_view()),
    path('register/', include('dj_rest_auth.registration.urls')),
    path('send-mobile-verification-otp/', SendMobileVerificationOTP.as_view(), name='send-mobile-verification-otp'),
    path('verify-mobile-verification-otp/', VerifyMobileVerificationOTP.as_view(), name='verify-mobile-verification-otp'),
    path('change-email/', ChangeEmailView.as_view(), name='change-email'),
    path('change-mobile/', ChangeMobileNumberView.as_view(), name='change-mobile'),
    path('update-mobile/', UpdateMobileNumberView.as_view(), name='update-mobile'),
    path('confirm-update-mobile/', UpdateMobileNumberConfirmView.as_view(), name='confirm-update-mobile'),
    path('auth/', include('dj_rest_auth.urls')),
    path('user-details/', UserDetailsView.as_view()),
    path('seller-dashboard-stats/', SellerDashboardStats.as_view(), name='seller_dashboard_stats'),
    path('seller-state-orders/', SellerStateOrders.as_view(), name='seller_state_orders'),
    path("request-forget-password/",RequestForgetPassword.as_view(),name="request-forget-password"),
    path('password-reset-email-confirm/', PasswordResetEmailConfirmView.as_view(),
        name='password-reset-email-confirm'),
    path('password-reset-mobile-confirm/', PasswordResetMobileConfirmView.as_view(),
        name='password-reset-mobile-confirm'),
]

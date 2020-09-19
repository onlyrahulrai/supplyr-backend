
from django.contrib import admin
from django.urls import path, include
from rest_framework import routers
# from rest_framework_simplejwt.views import TokenRefreshView
# from rest_framework.authtoken.views import obtain_auth_token

from supplyr.core.views import UserDetailsView, CustomLoginView, SellerProfilingView, ProfilingDocumentsUploadView, CategoriesView, BuyerProfilingView

# router = routers.DefaultRouter()
# router.register(r'users', UserDetailsViewSet)

urlpatterns = [
    # path('', include(router.urls)),
    path('login/', CustomLoginView.as_view()),
    path('register/', include('dj_rest_auth.registration.urls')),
    # path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('dj-rest-auth/', include('dj_rest_auth.urls')),
    path('user-details/', UserDetailsView.as_view()),
    path('user-profiling/', SellerProfilingView.as_view()),
    path('buyer-profiling/', BuyerProfilingView.as_view()),
    path('user-profiling-documents/', ProfilingDocumentsUploadView.as_view()),
    path('categories/', CategoriesView.as_view()),
]

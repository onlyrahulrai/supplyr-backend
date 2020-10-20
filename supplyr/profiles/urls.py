from .views import AddressView
from django.urls import path

urlpatterns = [
    path('buyer-address/', AddressView.as_view(), name='buyer-adress'),
    path('buyer-address/<int:pk>', AddressView.as_view(), name='buyer-address-edit'),
]
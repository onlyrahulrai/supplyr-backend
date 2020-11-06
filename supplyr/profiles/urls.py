from .views import AddressView
from django.urls import path
from .views import *

urlpatterns = [
    path('buyer-address/', AddressView.as_view(), name='buyer-adress'),
    path('buyer-address/<int:pk>', AddressView.as_view(), name='buyer-address-edit'),
    path('sellers-list/', SellersListView.as_view(), name='sellers_list'),
    path('sellers/', SellerView.as_view(), name='sellers'),
    path('seller/<int:pk>/', SellerView.as_view(), name='seller'),
]
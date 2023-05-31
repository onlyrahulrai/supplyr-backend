from django.urls import path
from .views import *

urlpatterns = [
    path("seller-contact-with-buyers/",SellerContactWithBuyersAPIView.as_view(),name="seller-contact-with-buyers"),
    path("seller-contact-with-buyers/<str:buyer>/",SellerContactWithBuyerDetailAPIView.as_view(),name="seller-contact-with-buyer-detail"),
    path("",BuyerDiscountAPIView.as_view(),name="generic-discount"),
    path("<str:pk>/",BuyerDiscountAPIView.as_view(),name="generic-discount-retrive-update-delete"),
]
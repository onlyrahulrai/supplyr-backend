from os import name
from .views import AddressView
from django.urls import path
from .views import *

urlpatterns = [
    path("seller-profile-settings/",SellerProfileSettings.as_view(),name="seller-profile-settings"),
    path('resend-verification-email/', ResendEmailConfirmation.as_view(), name='resend-email-confirmation'),
    path('user-profiling/', SellerProfilingView.as_view()),
    path('user-profiling-documents/', ProfilingDocumentsUploadView.as_view()),
    path('buyer-profiling/', BuyerProfilingView.as_view()),
    path('buyer-address/', AddressView.as_view(), name='buyer-adress'),
    path('buyer-address/<int:pk>', AddressView.as_view(), name='buyer-address-edit'),
    path('sellers-list/', SellersListView.as_view(), name='sellers_list'),
    path('buyers-search/', BuyerSearchView.as_view(), name='buyers_search'),
    path('buyers-recent/', RecentBuyersView.as_view(), name='buyers_recent'),
    path('buyer-create/', CreateBuyerView.as_view(), name='buyer_create'),
    # path('buyer-details/<str:pk>/', BuyerDetailsView.as_view(), name='buyer_details'),
    path('sellers/', SellerView.as_view(), name='sellers'),
    path('seller/<int:pk>/', SellerView.as_view(), name='seller'),
    path('categories/', ProfilingCategoriesView.as_view()),
    path('salespersons/', SalespersonView.as_view(), name='salespersons'),
    path('salespersons/<int:pk>/', SalespersonView.as_view(), name='salesperson'),
    path('apply-for-approval/', ApplyForApproval.as_view(), name='apply-for-approval'),
    
    ############################# Seller Address ##########################
    
    path('seller-address/', SellerAddressView.as_view(), name='seller-adress-create'),
    path('seller-address/<str:pk>/', SellerAddressView.as_view(), name='seller-adress-update'),
    path("gst-config-setting/",GstConfigSettingAPIView.as_view(),name="gst-config-setting")
    
    ############################# Seller Address ##########################
]
from .views import AddressView
from django.urls import path
from .views import *

urlpatterns = [
    path('user-profiling/', SellerProfilingView.as_view()),
    path('user-profiling-documents/', ProfilingDocumentsUploadView.as_view()),
    path('buyer-profiling/', BuyerProfilingView.as_view()),
    path('buyer-address/', AddressView.as_view(), name='buyer-adress'),
    path('buyer-address/<int:pk>', AddressView.as_view(), name='buyer-address-edit'),
    path('sellers-list/', SellersListView.as_view(), name='sellers_list'),
    path('buyers-search/', BuyerSearchView.as_view(), name='buyers_search'),
    path('buyers-recent/', RecentBuyersView.as_view(), name='buyers_recent'),
    path('sellers/', SellerView.as_view(), name='sellers'),
    path('seller/<int:pk>/', SellerView.as_view(), name='seller'),
    path('categories/', ProfilingCategoriesView.as_view())
]
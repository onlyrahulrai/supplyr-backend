from django.urls import path

from .views import *

urlpatterns = [
    path(
        '',
        OrderView.as_view(),
        name='order'
    ),
    path(
        '<str:pk>/update/',
        OrderView.as_view(),
        name='order'
    ),
    path(
        'list/',
        OrderListView.as_view(),
        name='orders_list'
    ),
    path(
        '<int:pk>/', 
        OrderDetailsView.as_view(), 
        name='order_details'
    ),
    path(
        'bulk-update/', 
        OrdersBulkUpdateView.as_view(), 
        name='orders_bulk_update'
    ),
    path('cancel/',
        OrderCancellationView.as_view(),
        name='orders_cancel'
    ),
]
from django.urls import path

from .views import *

urlpatterns = [
    path(
        '',
        OrderView.as_view(),
        name='order'
    ),
    path(
        'list/',
        OrderListView.as_view(),
        name='orders_list'
    ),
]
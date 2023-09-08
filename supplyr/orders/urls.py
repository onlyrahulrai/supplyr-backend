from django.urls import path

from .views import *

urlpatterns = [
    path("invoice-templates/",InvoiceTemplateView.as_view(),name="invoice-templates"),
    path("generate-invoice/",GenerateInvoiceView.as_view(),name="generate-invoice"),
    path("transaction/",PaymentCreateAPIView.as_view(),name="transaction-create"),
    path("ledgers/<str:pk>/",LedgerAPIView.as_view(),name="ledgers"),
    path("order-status-variable/<str:orderId>/<str:pk>/",OrderStatusVariableAPIView.as_view(),name="order-status-variable"),
    path("product/<str:pk>/",ProductDetailView.as_view(),name="order-product-detail"),
    path(
        'list/',
        OrderListView.as_view(),
        name='orders_list'
    ),
    path(
        'bulk-update/', 
        OrdersBulkUpdateView.as_view(), 
        name='orders_bulk_update'
    ),
    path(
        'bulk-update-orderitems/<str:orderId>/', 
        BulkUpdateOrderItemsView.as_view(), 
        name='bulk-update-orderitems'
    ),
    path('cancel/',
        OrderCancellationView.as_view(),
        name='orders_cancel'
    ),
    path(
        '<str:pk>/mark-as-paid/',
        MarkAsOrderPaidView.as_view(),
        name='mark-as-paid'
    ),
    path(
        '<str:pk>/update/',
        OrderView.as_view(),
        name='order'
    ),
    path(
        '<int:pk>/', 
        OrderDetailsView.as_view(), 
        name='order_details'
    ),
    path(
        '',
        OrderView.as_view(),
        name='order'
    ),
]
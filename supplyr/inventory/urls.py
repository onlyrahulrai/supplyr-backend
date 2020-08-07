from django.urls import path
from .views import AddProduct, ProductDetails

urlpatterns = [
    path('add-product/', AddProduct.as_view(), name='add_product'),
    path('product/<int:id>', ProductDetails.as_view(), name='product_details'),
]
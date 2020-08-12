from django.urls import path
from .views import AddProduct, ProductDetails, ProductImageUpload, ProductListView

urlpatterns = [
    path('add-product/', AddProduct.as_view(), name='add_product'),
    path('add-product-image/', ProductImageUpload.as_view(), name='add_product_image'),
    path('products/', ProductListView.as_view(), name='products_list'),
    path('product/<int:id>', ProductDetails.as_view(), name='product_details'),
]
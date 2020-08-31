from django.urls import path
from .views import AddProduct, ProductDetails, ProductImageUpload, ProductListView, DeleteProduct, CategoriesView, ProductsBulkUpdateView

urlpatterns = [
    path('add-product/', AddProduct.as_view(), name='add_product'),
    path('add-product-image/', ProductImageUpload.as_view(), name='add_product_image'),
    path('products/', ProductListView.as_view(), name='products_list'),
    path('products/bulk-update/', ProductsBulkUpdateView.as_view(), name='products_bulk_update'),
    path('product/<int:id>', ProductDetails.as_view(), name='product_details'),
    path('delete/', DeleteProduct.as_view(), name='delete_product'),
    path('categories/', CategoriesView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoriesView.as_view(), name='category'),
]
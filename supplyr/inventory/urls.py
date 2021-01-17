from django.urls import path
from .views import AddProduct, ProductDetails, ProductImageUpload, SellerSelfProductListView, SellerProductListView, DeleteProduct, CategoriesView, ProductsBulkUpdateView, \
    VariantDetailView, UpdateFavouritesView

urlpatterns = [
    path('add-product/', AddProduct.as_view(), name='add_product'),
    path('add-product-image/', ProductImageUpload.as_view(), name='add_product_image'),
    path('products/', SellerSelfProductListView.as_view(), name='products_list'),
    path('products-by-seller/<int:seller_id>', SellerProductListView.as_view(), name='products_list'),
    path('products/bulk-update/', ProductsBulkUpdateView.as_view(), name='products_bulk_update'),
    path('product/<int:id>', ProductDetails.as_view(), name='product_details'),
    path('product/<slug>', ProductDetails.as_view(), name='product_details'),
    path('delete/', DeleteProduct.as_view(), name='delete_product'),
    path('categories/', CategoriesView.as_view(), name='categories'),
    path('categories/<int:pk>/', CategoriesView.as_view(), name='category'),
    
    path('cart-items-info/', VariantDetailView.as_view(), name='variants_details'),
    path('update-favourites/', UpdateFavouritesView.as_view()),
]
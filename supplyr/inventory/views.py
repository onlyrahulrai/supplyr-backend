from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, mixins
from rest_framework.generics import ListAPIView, GenericAPIView

from supplyr.core.permissions import IsApproved
from .serializers import ProductDetailsSerializer, ProductImageSerializer, ProductListSerializer
from supplyr.core.serializers import CategoriesSerializer2
from supplyr.core.models import Category
from .models import Product, Variant, ProductImage
from django.db.models import Prefetch, Q, Count

class AddProduct(APIView):
    permission_classes = [IsApproved]
    def post(self, request, *args, **kwargs):
        
        # print(request.data)
        profile = request.user.profiles.first()
        
        if product_id := request.data.get('id'):
            product = get_object_or_404(Product, pk=product_id, owner = profile)
            product_serializer = ProductDetailsSerializer(product, data = request.data)
        else:
            product_serializer = ProductDetailsSerializer(data = request.data)

        if product_serializer.is_valid():
            product = product_serializer.save(owner = profile)


        return Response({"product": product_serializer.data})

class DeleteProduct(APIView):
    permission_classes = [IsApproved]

    def post(self, request, *args, **kwargs):
        profile = request.user.profiles.first()
        if product_id := request.data.get('id'):
            product = get_object_or_404(Product, pk=product_id, owner = profile)
            product.is_active = False
            product.save()
            return Response({
                "success": True,
            })
        return Response({"success": False}, status=400)

class ProductDetails(APIView):
    permission_classes = [IsApproved]

    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("id")
        product = get_object_or_404(Product, id=product_id, is_active = True)
        product_serializer = ProductDetailsSerializer(product)
        return Response(product_serializer.data)

class ProductImageUpload(APIView):
    permission_classes = [IsApproved]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        
        data = request.data
        # data['uploaded_by'] = request.user.profiles.first().pk

        serializer = ProductImageSerializer(data = data)

        serializer.is_valid(raise_exception=True)
        serializer.save(uploaded_by = request.user.profiles.first())
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductListView(ListAPIView):
    permission_classes = [IsApproved]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        profile = self.request.user.profiles.first()
        print('RG', (self.request.query_params))
        filters = {}
        if search_query := self.request.GET.get('search'):
            filters['title__search'] = search_query
        if sub_categories  := self.request.GET.get('sub_categories'):
            filters['sub_categories__in'] = sub_categories.split(',')

        print('filters', filters)
        return Product.objects.filter(owner = profile, is_active = True, **filters)\
            .annotate(variants_count_annotated=Count('variants', filter=Q(variants__is_active=True)))\
            .prefetch_related(
                 Prefetch('images', queryset=ProductImage.objects.filter(is_active=True), to_attr='active_images_prefetched'),
                 Prefetch('variants', queryset=Variant.objects.filter(is_active=True), to_attr='active_variants_prefetched'),
                 )
                 # Didn't store annotations and prefetches into their natural names, as the model methods could fail if these has not been generated. 
                 # Hence, stored them with unique names which I am checking in models, to use if exists.

class ProductsBulkUpdateView(APIView):
    permission_classes = [IsApproved]

    def post(self, request, *args, **kwargs):
        operation = request.data.get('operation')
        profile = request.user.profiles.first()

        if operation in ['add-subcategories', 'remove-subcategories']:
            product_ids = request.data.get('product_ids')
            sub_categories_list = request.data.get('data')

            for product in Product.objects.filter(pk__in = product_ids, owner=profile, is_active = True):
                if operation == 'add-subcategories':
                    product.sub_categories.add(*sub_categories_list)
                else:
                    product.sub_categories.remove(*sub_categories_list)
        
        return Response({'success': True})


class CategoriesView(GenericAPIView, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin):
    queryset = Category.objects.filter(is_active =True)
    serializer_class = CategoriesSerializer2
    permission_classes = [IsApproved]
    # parser_classes = [FormParser, MultiPartParser]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        if kwargs.get('pk'):
            return super().retrieve(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        if category_id := kwargs.get('pk'):
            # category_instance = get_object_or_404(Category, id=category_id)
            return super().update(request, *args, **kwargs)
        return super().create(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        if category_id := kwargs.get('pk'):
            category = Category.objects.filter(pk=category_id).update(is_active = False)
            return Response(None, status=204)
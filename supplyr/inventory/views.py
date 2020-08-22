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
from .models import Product

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
        return Product.objects.filter(owner = profile, is_active = True)


class CategoriesView(GenericAPIView, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin):
    queryset = Category.objects.filter(is_active =True)
    serializer_class = CategoriesSerializer2
    permission_classes = [IsApproved]
    pagination_class = None

    def get(self, request, *args, **kwargs):
        if id := kwargs.get('pk'):
            return super().retrieve(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
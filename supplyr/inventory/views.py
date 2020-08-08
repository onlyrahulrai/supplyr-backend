from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status

from supplyr.core.permissions import IsApproved
from .serializers import ProductDetailsSerializer, ProductImageSerializer
from .models import Product

class AddProduct(APIView):
    permission_classes = [IsApproved]
    def post(self, request, *args, **kwargs):
        # product = Product.objects.first()
        print(request.data)
        profile = request.user.profiles.first()
        product_serializer = ProductDetailsSerializer(data = request.data)
        if product_serializer.is_valid():
            product = product_serializer.save(owner = profile)


        return Response({"product": product_serializer.data})

class ProductDetails(APIView):
    permission_classes = [IsApproved]

    def get(self, request, *args, **kwargs):
        product_id = kwargs.get("id")
        product = get_object_or_404(Product, id=product_id)
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
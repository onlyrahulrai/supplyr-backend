from django.shortcuts import render, get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response

from supplyr.core.permissions import IsApproved
from .serializers import ProductDetailsSerializer
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

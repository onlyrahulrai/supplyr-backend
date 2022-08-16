from rest_framework import generics
from supplyr.inventory.utils import CustomPageNumberPagination
from supplyr.utils.api.mixins import UserInfoMixin
from django.http.response import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework import status, mixins
from rest_framework.generics import ListAPIView, GenericAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated

from supplyr.core.permissions import IsApproved, IsFromBuyerAPI, IsFromBuyerOrSalesAPI, IsFromSellerAPI, IsFromBuyerSellerOrSalesAPI
from .serializers import *
from supplyr.inventory.models import Category,BuyerDiscount
from supplyr.profiles.models import BuyerProfile,  SellerProfile
from .models import Product, Variant, ProductImage
from django.db.models import Prefetch, Q, Count, Sum, Min, Max

class AddProduct(APIView,UserInfoMixin):
    permission_classes = [IsApproved]
    def post(self, request, *args, **kwargs):
        
        # print("\n\n\n product data \n\n\n",request.data)
        profile = request.user.seller_profiles.first()
        
        if product_id := request.data.get('id'):
            product = get_object_or_404(Product, pk=product_id, owner = profile)
            product_serializer = ProductDetailsSerializer(product, data = request.data)
        else:
            product_serializer = ProductDetailsSerializer(data = request.data)

        if product_serializer.is_valid():
            product = product_serializer.save(owner = profile)

        response = self.inject_user_info(product_serializer.data, request.user)

        return Response({"product": response })

class DeleteProduct(APIView):
    permission_classes = [IsApproved]

    def post(self, request, *args, **kwargs):
        profile = request.user.seller_profiles.first()
        if product_id := request.data.get('id'):
            product = get_object_or_404(Product, pk=product_id, owner = profile)
            product.is_active = False
            product.save()
            
            variants = Variant.objects.filter(product=product_id).update(is_active=False)
            
            buyerDiscounts = BuyerDiscount.objects.filter(product=product_id).update(is_active=False)
            
            return Response({
                "success": True,
            })
        return Response({"success": False}, status=400)

class ProductDetails(APIView,UserInfoMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        if slug:=kwargs.get('slug'):
            product = get_object_or_404(Product, slug=slug, is_active = True)
        elif product_id := kwargs.get('id'):
            product = Product.objects.filter(slug=product_id, is_active = True).first() # In case slug/product title is numeric
            if not product:
                product = get_object_or_404(Product, id=product_id, is_active = True)

        product_serializer = ProductDetailsSerializer(product, context={'request' : request})
        response = self.inject_user_info(product_serializer.data,request.user)
        return Response(response)

class ProductImageUpload(APIView):
    permission_classes = [IsApproved]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request, *args, **kwargs):
        
        data = request.data
        # data['uploaded_by'] = request.user.seller_profiles.first().pk

        serializer = ProductImageSerializer(data = data)

        serializer.is_valid(raise_exception=True)
        serializer.save(uploaded_by = request.user.seller_profiles.first())
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class SellerSelfProductListView(ListAPIView):
    """
    Products list of a seller when viewed by himself
    """
    permission_classes = [IsApproved]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        profile = self.request.user.seller_profiles.first()
        print('RG', (self.request.query_params))
        filters = {}
        if search_query := self.request.GET.get('search'):
            filters['title__search'] = search_query
        if sub_categories  := self.request.GET.get('sub_categories'):
            filters['sub_categories__in'] = sub_categories.split(',')

        print('filters', filters)
        sorting = self.request.GET.get("order_by","-created_at")
        return Product.objects.filter(owner = profile, is_active = True, **filters)\
            .annotate(
                variants_count_annotated=Count('variants', filter=Q(variants__is_active=True)),
                quantity_all_variants=Sum('variants__quantity', filter=Q(variants__is_active=True)),
                sale_price_minimum=Min('variants__price', filter=Q(variants__is_active=True)),
                sale_price_maximum=Max('variants__price', filter=Q(variants__is_active=True))
                )\
            .prefetch_related(
                 Prefetch('images', queryset=ProductImage.objects.filter(is_active=True), to_attr='active_images_prefetched'),
                 Prefetch('variants', queryset=Variant.objects.filter(is_active=True), to_attr='active_variants_prefetched'),
                 ).order_by(sorting)
                 # Didn't store annotations and prefetches into their natural names, as the model methods could fail if these has not been generated. 
                 # Hence, stored them with unique names which I am checking in models, to use if exists.
class ProductListView(ListAPIView):
    """
    Products list of a seller when viewed by himself
    """
    permission_classes = [IsApproved]
    serializer_class = ProductListSerializer
    pagination_class = None

    def get_queryset(self):
        profile = self.request.user.seller_profiles.first()
        return Product.objects.filter(owner = profile, is_active = True)
                 
class SellerSelfproductDetailView(RetrieveAPIView):
    permission_classes = [IsApproved]
    serializer_class = ProductListSerializer
    lookup_field = "pk"


class SellerProductListView(ListAPIView):
    """
    Products list of a seller, when viewed by a buyer
    """
    permission_classes = [IsFromBuyerOrSalesAPI]
    serializer_class = ProductListSerializer

    def get_queryset(self):
        seller_id = self.kwargs.get('seller_id')
        is_favourites_required = self.request.GET.get('favourites')
        profile = SellerProfile.objects.get(id=seller_id)
        filters = {}

        if is_favourites_required:
            buyer_profile = self.request.user.buyer_profiles.first()
            return buyer_profile.favourite_products.filter(owner = profile)
        # if search_query := self.request.GET.get('search'):
        #     filters['title__search'] = search_query
        if sub_categories  := self.request.GET.get('sub_categories'):
            filters['sub_categories__in'] = sub_categories.split(',')

        # print('filters', filters)
        return Product.objects.filter(owner = profile, is_active = True, **filters)\
            .annotate(variants_count_annotated=Count('variants', filter=Q(variants__is_active=True), distinct=True))\
            .prefetch_related(
                 Prefetch('images', queryset=ProductImage.objects.filter(is_active=True), to_attr='active_images_prefetched'),
                 Prefetch('variants', queryset=Variant.objects.filter(is_active=True), to_attr='active_variants_prefetched'),
                 )
                 # Didn't store annotations and prefetches into their natural names, as the model methods could fail if these has not been generated. 
                 # Hence, stored them with unique names which I am checking in models, to use if exists.

class VariantDetailView(ListAPIView):
    """
    Passed a list of variant IDs, it will return a list of detailed variants information
    Made for used in cart where list of variant IOs is maintained on frontend and details need to be fetched from backend.
    """
    permission_classes = [IsFromBuyerSellerOrSalesAPI]
    serializer_class = VariantDetailsSerializer
    pagination_class = None

    def get_queryset(self):
        variant_ids_str = self.request.GET.get('variant_ids').split(',')
        variant_ids = list(map(int, variant_ids_str))
        print("VR  ",variant_ids)
        return Variant.objects.filter(id__in=variant_ids)

class ProductsBulkUpdateView(APIView):
    permission_classes = [IsApproved]

    def post(self, request, *args, **kwargs):
        operation = request.data.get('operation')
        profile = request.user.seller_profiles.first()

        if operation in ['add-subcategories', 'remove-subcategories']:
            product_ids = request.data.get('product_ids')
            sub_categories_list = request.data.get('data')

            for product in Product.objects.filter(pk__in = product_ids, owner=profile, is_active = True):
                if operation == 'add-subcategories':
                    product.sub_categories.add(*sub_categories_list)
                else:
                    product.sub_categories.remove(*sub_categories_list)
        
        return Response({'success': True})

class CategoriesDetailView(GenericAPIView,mixins.RetrieveModelMixin,mixins.UpdateModelMixin,UserInfoMixin):
    serializer_class = CategoriesSerializer2
    permission_classes = [IsApproved]
    # parser_classes = [FormParser, MultiPartParser]
    pagination_class = None
    
    def get_queryset(self):
        try:
            seller_profile = self.request.user.seller_profiles.first()
        except:
            seller_profile = None
        return Category.objects.filter(is_active=True).filter(Q(seller=seller_profile))
    
    def get(self, request, *args, **kwargs):
        # if kwargs.get('pk'):
        return super().retrieve(request, *args, **kwargs)
        # return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("request data :  -----> ",request.data)
        response = None
        if category_id := kwargs.get('pk'):
            # category_instance = get_object_or_404(Category, id=category_id)
            response = self.inject_user_info(super().update(request, *args, **kwargs).data, request.user)
        return Response(response)
        
            
    
    def delete(self, request, *args, **kwargs):
        if category_id := kwargs.get('pk'):
            category = Category.objects.filter(pk=category_id).update(is_active = False)
            return Response(None, status=204)
    
class CategoriesView(GenericAPIView, mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.CreateModelMixin, UserInfoMixin):
    """
    View for viewing, adding, updating, and deleting categories and subcategories
    """
    serializer_class = CategoriesSerializer2
    permission_classes = [IsApproved]
    # parser_classes = [FormParser, MultiPartParser]
    pagination_class = None
    
    def get_queryset(self):
        try:
            seller_profile = self.request.user.seller_profiles.first()
        except:
            seller_profile = None
        return Category.objects.filter(is_active=True,parent=None).filter(Q(seller=seller_profile))
         

    def get(self, request, *args, **kwargs):
        # if kwargs.get('pk'):
        #     return super().retrieve(request, *args, **kwargs)
        return super().list(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        print("requested data ------>:",request.data)
        # if category_id := kwargs.get('pk'):
        #     # category_instance = get_object_or_404(Category, id=category_id)
        #     response =  super().update(request, *args, **kwargs)
        # else: 
        #     response = super().create(request, *args, **kwargs)
        response = self.inject_user_info(super().create(request, *args, **kwargs).data, request.user)
        return Response(response)
        
            
    
    # def delete(self, request, *args, **kwargs):
    #     if category_id := kwargs.get('pk'):
    #         category = Category.objects.filter(pk=category_id).update(is_active = False)
    #         return Response(None, status=204)

class UpdateFavouritesView(APIView):
    permission_classes = [IsAuthenticated, IsFromBuyerAPI]

    def post(self, request, *args, **kwargs):
        operation = request.data.get('operation')
        product_id = request.data.get('product_id')

        try:
            print(request.data, product_id, operation)
            profile = request.user.buyer_profiles.first()
            product = Product.objects.get(id=int(product_id))

            if operation == 'add':
                profile.favourite_products.add(product)
            elif operation == 'remove':
                profile.favourite_products.remove(product)

            return Response({'success': True})

        except Exception as e:
            print("Enterrd excepitopn", str(e))
            return Response({'success': False, 'message': str(e)}, status=500)
        

class SellerBuyersDetailAPIView(APIView):
    permission_classes = [IsApproved,IsFromSellerAPI]
    
    def get(self,request,*args,**kwargs):
        if pk := kwargs.get("pk",None):
            object = request.user.seller_profiles.first().connections.filter(Q(buyer__pk=pk)).first()
            buyer = get_object_or_404(BuyerProfile,pk=object.buyer.id)
            serializer = BuyerDetailForDiscountSerializer(buyer)
            return Response(serializer.data,status=status.HTTP_200_OK)        

############## Buyer Discount Start ############
class BuyerSellerConnectionAPIView(GenericAPIView,mixins.ListModelMixin):
    permission_classes = [IsApproved,IsFromSellerAPI]
    serializer_class = BuyerSellerConnectionSerializers
    pagination_class = CustomPageNumberPagination
    
    def get_queryset(self):
        query = self.request.GET.get("search",None)
        seller = self.request.user.seller_profiles.first()
        if(query):
            buyers = seller.connections.filter((Q(buyer__business_name__icontains=query) | Q(buyer__owner__email__icontains=query)) & Q(is_active=True))
        else:
            buyers = seller.connections.filter(is_active=True)
        return buyers
    
    def get(self,request,*args,**kwargs):
        return self.list(request,*args,**kwargs)
class SellerBuyersAPIView(ListAPIView,RetrieveAPIView):
    permission_classes = [IsApproved,IsFromSellerAPI]
    serializer_class = SellerBuyersConnectionSerializer
    
    def get_queryset(self):
        query = self.request.GET.get("search",None)
        seller = self.request.user.seller_profiles.first()

        connections = seller.connections.filter(Q(is_active=True))
            
        buyerIDs = [connection.buyer.id for connection in connections]
        
        profiles = BuyerProfile.objects.filter(id__in=buyerIDs)
        
        if query:
            profiles = profiles.filter(Q(business_name__icontains=query) | Q(owner__email__icontains=query) | Q(owner__mobile_number__icontains=query) | Q(manuallycreatedbuyer__email__icontains=query) | Q(manuallycreatedbuyer__mobile_number__icontains=query)).prefetch_related('manuallycreatedbuyer_set')
            
        return profiles
    
    def get(self,request,*args,**kwargs):
        if self.kwargs.get("pk"):
            return self.retrieve(request,*args,**kwargs)
        return self.list(request,*args,**kwargs)

# class BuyerSellerConnectionAPIView(APIView):
#     permission_classes = [IsApproved,IsFromSellerAPI]
    
#     def get(self,request,*args,**kwargs):
#         seller = request.user.seller_profiles.first()
#         query = request.GET.get("search",None)
#         pagination = request.GET.get("pagination")
#         print(f' Pagination ----> {pagination} ')
#         if(query):
#             buyers = seller.connections.filter((Q(buyer__business_name__icontains=query) | Q(buyer__owner__email__icontains=query)) & Q(is_active=True))
#         else:
#             buyers = seller.connections.filter(is_active=True)
#         paginator = CustomPageNumberPagination()
#         paginator.page_size = buyers.count() if not pagination else 8
#         result_page = paginator.paginate_queryset(buyers, request)
#         serializers = BuyerSellerConnectionSerializers(result_page,many=True)
#         return paginator.get_paginated_response(serializers.data)
    
class BuyerDetailForDiscountAPIView(APIView):
    permission_classes = [IsFromSellerAPI]
    
    def get(self,request,*args,**kwargs):
        if pk := kwargs.get("pk"):
            # seller_profile = get_object_or_404(SellerProfile,is_active=True,owner=request.user)
            buyer_profile = get_object_or_404(BuyerProfile,pk=pk,is_active=True)
            serializer = BuyerDetailForDiscountSerializer(buyer_profile)
            return Response(serializer.data,status=status.HTTP_200_OK)
        
class BuyerDiscountAPIView(APIView):
    permission_classes = [IsFromSellerAPI]
    
    def post(self,request,*args,**kwargs):
        if request.data.get("setting") == "generic_discount":
            if pk := request.data.get("data").get("id"):
                discount = get_object_or_404(BuyerDiscount,pk=pk)
                serializer = GenericDiscountSerializer(discount,data=request.data.get("data"))
            else:
                serializer = GenericDiscountSerializer(data=request.data.get("data"))
                
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
        if request.data.get("setting") == "product_based_discount":
            if pk := request.data.get("data").get("id"):
                discount = get_object_or_404(BuyerDiscount,pk=pk)
                serializer = ExclusiveProductDiscountSerializer(discount,data=request.data.get("data"))
            else:
                serializer = ExclusiveProductDiscountSerializer(data=request.data.get("data"))
                
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data,status=status.HTTP_200_OK)
            return Response(serializer.errors,status=status.HTTP_400_BAD_REQUEST)
        
    def delete(self,request,*args,**kwargs):
        if pk := kwargs.get("pk"):
            discount = get_object_or_404(BuyerDiscount,pk=pk)
            discount.is_active = False
            discount.save()
            return Response({"message":"success"},status=status.HTTP_202_ACCEPTED)
############## Buyer Discount End ############

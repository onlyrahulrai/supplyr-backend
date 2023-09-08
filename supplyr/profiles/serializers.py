from django.db.models.query_utils import Q
from rest_framework import serializers
from .models import AddressState, BuyerAddress, BuyerProfile, SellerProfile, SalespersonProfile,SellerAddress,CategoryOverrideGst
from django.contrib.auth import get_user_model
from typing import Dict
from supplyr.inventory.models import Category, Tags
from supplyr.inventory.serializers import CategoriesSerializer2, SubCategorySerializer2, SubCategorySerializer, TagsSerializer, VendorsSerializer
from supplyr.orders.models import OrderStatusVariable
from itertools import groupby
from supplyr.discounts.serializers import GenericDiscountSerializer,DiscountAssignedProductForBuyerSerializer

User = get_user_model()

class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]

    # def to_internal_value(self, data):
    #     # To support inserts with the value
    #     if data == '' and self.allow_blank:
    #         return ''

    #     for key, val in self._choices.items():
    #         if val == data:
    #             return key
    #     self.fail('invalid_choice', input=data)

class OrderStatusVariableForSeller(serializers.ModelSerializer):
    linked_order_status = serializers.CharField(source="linked_order_status.slug")
    class Meta:
        model = OrderStatusVariable
        fields = ( 'name', 'id', 'data_type','slug','linked_order_status')

class AddressStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressState
        fields = '__all__'

class SellerAddressSerializer(serializers.ModelSerializer):
    state = AddressStatesSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(queryset=AddressState.objects.all(), source='state', write_only=True)
    
    class Meta:
        model = SellerAddress
        exclude = ['owner','is_active','created_at',"updated_at"]
    
class ShortEntityDetailsSerializer(serializers.ModelSerializer):
    """
    To be used by seller app 
    (may be rename it to SellerProfileSerializer?)
    """
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, profile):
        sub_categories = profile.operational_fields.filter(is_active=True)
        # parent_category_list = []
        
        # for sub_category in sub_categories:
        #     if sub_category.parent not in parent_category_list:
        #         parent_category_list.append(sub_category.parent)
        
        # category_list = list(sub_categories) + parent_category_list

        sub_categories_serializer = SubCategorySerializer2(sub_categories, many=True)
        return sub_categories_serializer.data
    
    
    tags = serializers.SerializerMethodField()
    def get_tags(self,profile):
        tags = profile.tags.all()
        tag_serializer = TagsSerializer(tags,many=True)
        return tag_serializer.data
    
    vendors = serializers.SerializerMethodField()
    def get_vendors(self,profile):
        vendors = profile.vendors.all()
        vendors_serializer = VendorsSerializer(vendors,many=True)
        return vendors_serializer.data

    order_status_variables = serializers.SerializerMethodField()
    def get_order_status_variables(self,profile):
        # Group by order status
        data = OrderStatusVariableForSeller(profile.order_status_variables.all(), many=True).data
        data_sorted = sorted(data, key=lambda x: x['linked_order_status'])
        _data_grouped = groupby(data_sorted, key = lambda x: x['linked_order_status'])
        data_grouped = {k: list(v) for k,v in _data_grouped}
        return data_grouped

    addresses = serializers.SerializerMethodField()
    def get_addresses(self,profile):
        print(profile.seller_addresses.all())
        return SellerAddressSerializer(profile.seller_addresses.first()).data

    class Meta:
        model = SellerProfile
        fields = [
            'business_name',
            'id',
            "order_number_prefix",
            "default_currency",
            "currency_representation",
            "invoice_prefix",
            'connection_code',
            'gst_number',
            'default_gst_rate',
            'is_gst_enabled',
            'product_price_includes_taxes',
            "tags",
            "addresses",
            'user_settings',
            "invoice_template",
            "order_status_variables",
            "vendors",
            'sub_categories',
            'invoice_options',
            'order_status_options',
            'translations',
            ]
        extra_kwargs={
            "user_settings":{
                "write_only":True
            }
        }

class CategoriesSerializer(serializers.ModelSerializer):
    """
    Used for generating cateogries list for displaying in seller profiling form
    """
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, category):
        sub_categories = category.sub_categories.filter(is_active=True).filter(Q(seller=None) | Q(seller=self.context.get("seller")))
        return SubCategorySerializer(sub_categories, many=True).data
    # sub_categories = SubCategorySerializer(many=True)
    
    seller = serializers.SerializerMethodField()
    def get_seller(self,category):
        name = None
        try:
            name = category.seller.owner.name
        except:
            name = None
        return name

    class Meta:
        model = Category
        fields = [
            'name',
            'id',
            "seller",
            'sub_categories'
        ]
        depth = 1

def _get_seller_profiling_data(user: User) -> Dict:
    existing_profile = user.seller_profiles.first()
    entity_details = None
    profiling_data = None
    
    user_selected_sub_categories = []
    if  existing_profile:
        entity_details = SellerProfilingSerializer(existing_profile).data
        user_selected_sub_categories = existing_profile.operational_fields.all().values_list('id', flat=True)
        override_categories = CategoryOverrideGstSerializer(existing_profile.override_categories.filter(is_active=True),many=True).data

    ### Category Information
    # categories = Category.objects.filter(is_active=True).exclude(sub_categories = None)
    categories = Category.objects.filter(is_active=True,parent=None).filter(Q(seller=None) | Q(seller=existing_profile))
    cat_serializer = CategoriesSerializer(categories, many=True,context={"seller":existing_profile})
    cat_serializer_data = cat_serializer.data
    
   

    categories_data = {
            'categories': cat_serializer_data,
            'selected_sub_categories': user_selected_sub_categories
        }

    if not user.is_approved:
        profiling_data = {
            'entity_details': entity_details,
            'categories_data': categories_data
        }
    elif user.is_approved:
        profiling_data = {
            'categories_data': {**categories_data,'override_categories':override_categories}
        }
    
    return profiling_data

class BuyerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerProfile
        fields = [
            'id', 
            'business_name',
            'owner',
        ]
        extra_kwargs = {
            'owner': {
                'write_only': True
            }
        }

class UserDetailsSerializer(serializers.ModelSerializer):
    def _get_api_source(self):
        if 'request' in self.context:
            # requests will only be available is passed in extra context. dj-rest-auth passes in default views
            request = self.context['request']
            kwargs = request.resolver_match.kwargs
            if 'api_source' in kwargs:
                return kwargs['api_source']
        return None

    profiling_data = serializers.SerializerMethodField()
    def get_profiling_data(self, user):
        """
        Profiling data for people who are still filling the profiling form
        """
       
        return _get_seller_profiling_data(user) 

    
    profile = serializers.SerializerMethodField()
    def get_profile(self, user):
        """
        Profile details for people who are approved
        """

        if self._get_api_source() == 'buyer':
            if profile := user.buyer_profiles.first():
                return BuyerProfileSerializer(profile).data

        elif self._get_api_source() == 'sales':
            if profile := user.salesperson_profiles.first():
                return SalespersonProfileSerializer(profile).data

        elif user.is_approved: # seller profile
            profile = user.seller_profiles.first()
            return ShortEntityDetailsSerializer(profile).data
            
        return None

    user_status = serializers.SerializerMethodField()
    def get_user_status(self, user):
        if self._get_api_source() == 'buyer':
            return user.buyer_status
        elif self._get_api_source() == 'seller':
            return user.seller_status
        elif self._get_api_source() == 'sales':
            return user.salesperson_status
        
        return None
    
    user_profile_review = serializers.SerializerMethodField()
    def get_user_profile_review(self,user):
        review = None
        if seller_profile := user.seller_profiles.first():
            seller_profile_review = seller_profile.seller_profile_review.last()
            if(seller_profile_review):
                review = seller_profile_review.comments 
            return review
            


    user_role = serializers.SerializerMethodField()
    def get_user_role(self, user):
        if user.is_superuser:
            return "admin"
        elif user.is_staff:
            return "staff"
        return None

    class Meta:
        model = User
        fields = ["id",'name', 'first_name', 'last_name', 'username', 'is_staff', 'user_status','user_profile_review','profiling_data', 'profile', 'user_role', 'is_email_verified', 'is_mobile_verified', 'email', 'mobile_number']

class BuyerAddressSerializer(serializers.ModelSerializer):        

    state = AddressStatesSerializer(read_only=True)
    state_id = serializers.PrimaryKeyRelatedField(queryset=AddressState.objects.all(), source='state', write_only=True)
    class Meta:
        model = BuyerAddress
        # fields = '__all__'
        exclude = ['owner', 'state_old']

    # state = ChoiceField(choices=BuyerAddress.STATE_CHOICES)
          
class SellerProfilingSerializer(serializers.ModelSerializer):

    owner_name = serializers.SerializerMethodField()
    def get_owner_name(self,sellerprofile):
        return sellerprofile.owner.name
    
    owner_email = serializers.SerializerMethodField()
    def get_owner_email(self,sellerprofile):
        return sellerprofile.owner.email
    
    owner_phone = serializers.SerializerMethodField()
    def get_owner_phone(self,sellerprofile):
        return sellerprofile.owner.mobile_number
    
    class Meta:
        model = SellerProfile
        fields = [
            "id",
            "owner",
            "owner_name",
            "owner_email",
            "order_number_prefix",
            "owner_phone",
            'business_name',
            'entity_category',
            'entity_type',
            'is_gst_enabled',
            "invoice_prefix",
            'default_gst_rate',
            'gst_number',
            'user_settings',
            'invoice_template',
            'pan_number',
            "default_currency",
            "currency_representation",
            'tan_number',
            'gst_certificate',
            "status"
            ]

        read_only_fields = [
            'gst_certificate',
            'owner_name',
            'owner_email',
            'owner_phone'
        ]

        extra_kwargs = {
            'business_name': {
                'required': True,
                'allow_null': False,
                'allow_blank': False
            },
            'entity_category': {
                'required': True,
                'allow_null': False,
            },
            'entity_type': {
                'required': True,
                'allow_null': False,
                'allow_blank': False
            },
            "owner_name":{
                "read_only":True
            }
        }

class SellerProfilingDocumentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SellerProfile
        fields = [
            'owner',
            'gst_certificate'
            ]

class SellerShortDetailsForSalespersonSerializer(serializers.ModelSerializer):
    '''
    To be used by salesperson app
    '''

    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, profile):
        sub_categories = profile.operational_fields.filter(products__owner = profile, products__is_active=True).distinct()
        sub_categories_serializer = SubCategorySerializer2(sub_categories, many=True)
        return sub_categories_serializer.data

    has_products_added = serializers.SerializerMethodField()
    def get_has_products_added(self, seller):
        return seller.products.filter(is_active=True).exists()

    class Meta:
        model = SellerProfile
        fields = [
            'business_name',
            'sub_categories',
            'id',
            'has_products_added'
            ]
        
class ShortCategoryOverrideGstSerializer(serializers.ModelSerializer):
    class Meta:
        model = CategoryOverrideGst
        fields = "__all__"
        
class SellerShortDetailsForBuyerSerializer(SellerShortDetailsForSalespersonSerializer):
    '''
    To be used by buyer app
    '''
    
    generic_discount = serializers.SerializerMethodField()
    def get_generic_discount(self,profile): 
        buyer = self.context["request"].user.buyer_profiles.first()
        discount = profile.buyer_discounts.filter(Q(buyer=buyer) & Q(product=None) & Q(is_active=True)).first()
        return GenericDiscountSerializer(discount).data  if discount else None
    
    discount_assigned_products = serializers.SerializerMethodField()
    def get_discount_assigned_products(self, profile):
        buyer = self.context['request'].user.buyer_profiles.first()
        discounts = profile.buyer_discounts.filter(Q(buyer=buyer) & ~Q(product=None) & Q(is_active=True))
        return DiscountAssignedProductForBuyerSerializer(discounts, many=True).data 
    

    category_override_gst = serializers.SerializerMethodField()
    def get_category_override_gst(self,profile):
        override_categories = profile.override_categories.filter(Q(is_active=True))
        
        return ShortCategoryOverrideGstSerializer(override_categories,many=True).data

    class Meta:
        model = SellerProfile
        fields = [
            'business_name',
            'sub_categories',
            'id',
            'has_products_added',
            'generic_discount',
            'discount_assigned_products',
            "default_gst_rate",
            'category_override_gst',
            "product_price_includes_taxes"
            ]

class SalespersonProfileSerializer(serializers.ModelSerializer):
    """
    To be used in fetching user details in case of request from salesperson api.
    """

    seller = SellerShortDetailsForSalespersonSerializer()

    class Meta:
        model = SalespersonProfile
        fields = [
            'id',
            'seller'
            ]

class SalespersonProfileSerializer2(serializers.ModelSerializer):
    """
    To be used in fetching salespersons list in case of request from  seller api
    """

    name = serializers.SerializerMethodField()
    email = serializers.SerializerMethodField()
    is_joined = serializers.SerializerMethodField()

    def get_name(self, instance):
        if owner := instance.owner:
            return owner.name

    def get_is_joined(self, instance):
        if instance.owner:
            return True

    def get_email(self, instance):
        if owner := instance.owner:
            return owner.email
        if preregistered_user := instance.preregistrations.first():
            return preregistered_user.email



    class Meta:
        model = SalespersonProfile
        fields = [
            'id',
            'name',
            'email',
            'is_joined'
            ]

class CategoryOverrideGstSerializer(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    def get_category(self,gst):
        return {"id":gst.category.id,'name':gst.category.name,'is_parent':gst.category.is_parent}
    
    class Meta:
        model = CategoryOverrideGst
        fields = ['id','category','default_gst_rate']
                
class SellerGstConfigSettingSerializer(serializers.ModelSerializer):
    override_categories = serializers.SerializerMethodField()
    def get_override_categories(self,seller):
        return CategoryOverrideGstSerializer(seller.override_categories.all(),many=True).data
    
    class Meta:
        model = SellerProfile
        exclude = ["is_active","connection_code","created_at"]
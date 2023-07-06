from rest_framework import serializers
from django.db.models import Q
from supplyr.profiles.models import BuyerSellerConnection
from supplyr.inventory.models import (
    Product,
    BuyerDiscount,
    Variant
)
from supplyr.profiles.models import BuyerProfile, AddressState, BuyerAddress, ManuallyCreatedBuyer
from django.contrib.auth import get_user_model

User = get_user_model()


class AddressStatesSerializer(serializers.ModelSerializer):
    class Meta:
        model = AddressState
        fields = '__all__'


class BuyerAddressSerializerForSeller(serializers.ModelSerializer):
    # state = ChoiceField(choices=BuyerAddress.STATE_CHOICES)
    state = serializers.SerializerMethodField()

    def get_state(self, buyer_address):
        state = None
        if address := buyer_address.state:
            state = address.name
        return AddressStatesSerializer(buyer_address.state).data

    class Meta:
        model = BuyerAddress
        fields = ["id", "name", "line1", "line2", "pin", "city", "state"]


class VariantDetailsSerializer(serializers.ModelSerializer):
    class ProductShortDetailsSerializer(serializers.ModelSerializer):
        seller_name = serializers.CharField(source='owner.business_name')

        class Meta:
            model = Product
            fields = ["id", 'title', "slug", 'has_multiple_variants', 'sub_categories',
                      'id', 'seller_name', "allow_inventory_tracking", "allow_overselling"]

    title = serializers.SerializerMethodField()

    def get_title(self, variant):
        return variant.product.title

    featured_image = serializers.SerializerMethodField()

    def get_featured_image(self, variant):
        if variant.featured_image:
            return variant.featured_image.image_md.url

        if product_image := variant.product.featured_image:
            return product_image.image_md.url

        return None

    price = serializers.SerializerMethodField()

    def get_price(self, variant):
        return float(variant.price)

    actual_price = serializers.SerializerMethodField()

    def get_actual_price(self, variant):
        return float(variant.actual_price)

    product = ProductShortDetailsSerializer()

    class Meta:
        model = Variant
        exclude = ['created_at']


class DiscountAssignedProductSerializer(serializers.ModelSerializer):
    class ProductShortDetailsSerializer(serializers.ModelSerializer):
        featured_image = serializers.SerializerMethodField()

        def get_featured_image(self, product):
            if product.featured_image:
                return product.featured_image.image_md.url
            return None

        variants_data = serializers.SerializerMethodField()

        def get_variants_data(self, product):
            variants = product.variants.filter(is_active=True)
            if product.has_multiple_variants():
                data = VariantDetailsSerializer(variants, many=True).data
            else:
                data = VariantDetailsSerializer(variants.first()).data
            return data

        quantity = serializers.SerializerMethodField()

        def get_quantity(self, instance):
            return instance.default_variant.quantity

        class Meta:
            model = Product
            fields = ["id", 'title', "featured_image",
                      "variants_data", "quantity", "has_multiple_variants"]

    product = ProductShortDetailsSerializer()

    class Meta:
        model = BuyerDiscount
        fields = ["id", "product", "variant", "buyer", "seller",
                  "discount_type", "discount_value"]
        
class DiscountAssignedProductForBuyerSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDiscount
        fields = ["id", "product", "variant", "buyer", "seller",
                  "discount_type", "discount_value"]


class GenericDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDiscount
        fields = ["id", "seller", "buyer", "discount_type", "discount_value"]


class SellerContactWithBuyerSerializer(serializers.ModelSerializer):
    buyer = serializers.SerializerMethodField()

    def get_buyer(self, connection):
        name = connection.buyer.owner.name if connection.buyer.owner else ""
        email = connection.buyer.owner.email if connection.buyer.owner else connection.buyer.manuallycreatedbuyer_set.first().email
        mobile_number = connection.buyer.owner.mobile_number if connection.buyer.owner else connection.buyer.manuallycreatedbuyer_set.first().mobile_number

        return {"id": connection.buyer.id, "name": name, "email": email, "business_name": connection.buyer.business_name, "mobile_number": mobile_number}

    discount_assigned_products_length = serializers.SerializerMethodField()

    def get_discount_assigned_products_length(self, connection):
        seller = self.context['request'].user.seller_profiles.first()
        return len(connection.buyer.buyer_discounts.filter(Q(seller=seller) & Q(is_active=True) & ~Q(product=None)))

    generic_discount = serializers.SerializerMethodField()

    def get_generic_discount(self, connection):
        seller = self.context['request'].user.seller_profiles.first()
        generic_discount = connection.buyer.buyer_discounts.filter(
            Q(seller=seller) & Q(is_active=True) & Q(product=None)).first()
        data = GenericDiscountSerializer(
            generic_discount).data if generic_discount else 0
        return data

    class Meta:
        model = BuyerSellerConnection
        fields = ["id", "buyer", "generic_discount",
                  "discount_assigned_products_length"]


class SellerContactWithBuyerDetailSerializer(SellerContactWithBuyerSerializer):

    discount_assigned_products = serializers.SerializerMethodField()

    def get_discount_assigned_products(self, connection):
        seller = self.context['request'].user.seller_profiles.first()
        discounts = connection.buyer.buyer_discounts.filter(
            Q(seller=seller) & Q(is_active=True) & ~Q(product=None))
        return DiscountAssignedProductSerializer(discounts, many=True).data

    class Meta:
        model = BuyerSellerConnection
        fields = ["id", "buyer", "generic_discount",
                  "discount_assigned_products"]


class BuyerDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDiscount
        fields = ["id", "buyer", "seller", "product", "variant",
                  "discount_type", "discount_value", "is_active"]


class BuyerShortDetailSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, buyer):
        name = buyer.owner.name if buyer.owner else ""
        return name

    email = serializers.SerializerMethodField()

    def get_email(self, buyer):
        email = buyer.owner.email if buyer.owner else buyer.manuallycreatedbuyer_set.first().email
        return email

    mobile_number = serializers.SerializerMethodField()

    def get_mobile_number(self, buyer):
        mobile_number = buyer.owner.mobile_number if buyer.owner else buyer.manuallycreatedbuyer_set.first().mobile_number
        return mobile_number
    generic_discount = serializers.SerializerMethodField()

    def get_generic_discount(self, buyer):
        seller = self.context["request"].user.seller_profiles.first()
        discount = buyer.buyer_discounts.filter(Q(seller=seller) &
            Q(product=None), Q(variant=None), Q(is_active=True))
        if len(discount) > 0:
            return GenericDiscountSerializer(discount.first()).data
        return None

    product_discounts = serializers.SerializerMethodField()

    def get_product_discounts(self, buyer):
        seller = self.context["request"].user.seller_profiles.first()
        products = buyer.buyer_discounts.filter(
            Q(seller=seller) & ~Q(product=None) & Q(is_active=True))
        return DiscountAssignedProductSerializer(products, many=True).data

    address = serializers.SerializerMethodField()

    def get_address(self, buyer):
        addresses = buyer.buyer_address.filter(is_active=True)
        return BuyerAddressSerializerForSeller(addresses, many=True).data

    states = serializers.SerializerMethodField()

    def get_states(self, buyer):
        return AddressStatesSerializer(AddressState.objects.all(), many=True).data

    def to_internal_value(self, data):
        validated_data = super().to_internal_value(data)
        validated_data["email"] = data.get("email")
        validated_data["mobile_number"] = data.get("mobile_number")
        return validated_data

    def create(self, validated_data):
        email = validated_data.get('email')
        business_name = validated_data.get('business_name')
        mobile_number = validated_data.get('mobile_number')

        errors = {}
        if User.objects.filter(email__iexact=email).exists():
            errors['email'] = 'User already exist with this email ID'
        elif ManuallyCreatedBuyer.objects.filter(email__iexact=email).exists():
            errors['email'] = 'A buyer is already created with this email ID'

        if User.objects.filter(mobile_number=mobile_number).exists():
            errors['mobile_number'] = 'User Already exist with this mobile number'
        elif ManuallyCreatedBuyer.objects.filter(mobile_number=mobile_number):
            errors['mobile_number'] = 'A buyer is already created with this mobile number'

        if errors:
            raise serializers.ValidationError(errors)

        buyer_profile = BuyerProfile.objects.create(
            business_name=business_name,
        )
        profile = self.context["request"].user.get_seller_profile(
        ) if "seller" in self.context["request"].resolver_match.kwargs.values() else request.user.get_sales_profile()

        if "seller" in self.context["request"].resolver_match.kwargs.values():
            connection, created = BuyerSellerConnection.objects.get_or_create(
                buyer=buyer_profile, seller=profile)
            
            ManuallyCreatedBuyer.objects.create(
                buyer_profile=buyer_profile,
                email=email,
                mobile_number=mobile_number,
                created_by_seller=profile
            )
        else:
            ManuallyCreatedBuyer.objects.create(
                buyer_profile=buyer_profile,
                email=email,
                mobile_number=mobile_number,
                created_by=profile
            )
        return buyer_profile

    class Meta:
        model = BuyerProfile
        fields = ["id", "name", "email", "mobile_number", "business_name",
                  "address", "generic_discount", "product_discounts", 'states']

import os
import json
from django.http import request
from django_extensions.db import fields
from rest_framework import serializers

from supplyr.core.model_utils import get_auto_category_ORM_filters, get_wight_in_grams


from .models import AutoCategoryRule, Product, Tags, User, Variant, ProductImage, Category, Vendors,BuyerDiscount
from supplyr.profiles.models import BuyerAddress, BuyerProfile, BuyerSellerConnection, SellerProfile
from django.conf import settings
from django.db import transaction
from django.db.models.functions import Coalesce
from django.db.models import Q


class ChoiceField(serializers.ChoiceField):

    def to_representation(self, obj):
        if obj == '' and self.allow_blank:
            return obj
        return self._choices[obj]


class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'featured_image', 'price', 'actual_price', 'sale_price_minimum', 'sale_price_maximum', 'has_multiple_variants', 'quantity', 'quantity_all_variants', 'variants_count','variants_data' , 'default_variant_id', 'price_range',"sub_categories", 'actual_price_range', 'minimum_order_quantity',"allow_inventory_tracking","allow_overselling"]

    variants_data = serializers.SerializerMethodField()
    def get_variants_data(self,product):
        variants = product.variants.filter(is_active=True)
        if product.has_multiple_variants():
            print("multiple variants")
            data = VariantDetailsSerializer(variants,many=True).data
        else:
            data = VariantDetailsSerializer(variants.first()).data
        return  data

    featured_image = serializers.SerializerMethodField()
    def get_featured_image(self, instance):
        if image := instance.featured_image:
            if image_sm := image.image_sm:
                return image_sm.url
        return None

    actual_price = serializers.SerializerMethodField()
    def get_actual_price(self, instance):
        return instance.default_variant.actual_price

    price = serializers.SerializerMethodField()
    def get_price(self, instance):
        return instance.default_variant.price or instance.default_variant.actual_price

    sale_price_minimum = serializers.SerializerMethodField()
    def get_sale_price_minimum(self, instance):
        if hasattr(instance, 'sale_price_minimum'):
            return instance.sale_price_minimum
        return None

    sale_price_maximum = serializers.SerializerMethodField()
    def get_sale_price_maximum(self, instance):
        if hasattr(instance, 'sale_price_maximum'):
            return instance.sale_price_maximum
        return None


    quantity = serializers.SerializerMethodField()
    def get_quantity(self, instance):
        return instance.default_variant.quantity

    quantity_all_variants = serializers.SerializerMethodField()
    def get_quantity_all_variants(self, instance):
        if hasattr(instance, 'quantity_all_variants'):
            return instance.quantity_all_variants
        return None

    minimum_order_quantity = serializers.SerializerMethodField()
    def get_minimum_order_quantity(self, instance):
        return instance.default_variant.minimum_order_quantity

    default_variant_id = serializers.SerializerMethodField()
    def get_default_variant_id(self, instance):
        return instance.default_variant.id

    price_range = serializers.SerializerMethodField()
    def get_price_range(self, instance):
        if instance.has_multiple_variants():
            variants = instance.variants.filter(is_active=True).annotate(price_or_sale_price=Coalesce('price', 'actual_price')).order_by('price_or_sale_price')
            range = (variants.first().price_or_sale_price, variants.last().price_or_sale_price)
            return range

    actual_price_range = serializers.SerializerMethodField()
    def get_actual_price_range(self, instance):
        if instance.has_multiple_variants():
            variants = instance.variants.filter(is_active=True).order_by('price')
            range = (variants.first().actual_price, variants.last().actual_price)
            return range
        
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self,instance):
        return instance.sub_categories.values_list("id",flat=True)


class VariantSerializer(serializers.ModelSerializer):
    """
    To be used in productDetailsSerializer
    """

    def to_representation(self, instance):
        variant = super().to_representation(instance)
        if not variant['option1_name'] or (variant['option1_name'] == 'default' and variant['option1_value'] == 'default'):
            del variant['option1_name']
            del variant['option1_value']

        if not variant['option2_name']:
            del variant['option2_name']
            del variant['option2_value']

        if not variant['option3_name']:
            del variant['option3_name']
            del variant['option3_value']
            
            
            
        return variant

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        print("\n\n\n varient data \n\n\n ",data)
        if id := data.get('id'):
            internal_value['id'] = id
            
       
        return internal_value

    def create(self, validated_data):
        if id := validated_data.get('id'):  #For pre-existing variants, update rather than creating
            if variant := Variant.objects.get(id=id, product=validated_data.get('product')):
                return self.update(variant, validated_data)

        return super().create(validated_data)

    def update(self, variant, validated_data):
        variant_obj = super().update(variant, validated_data)
        if 'featured_image' not in validated_data and variant_obj.featured_image:
            # Featured image was earlier existed in variant, but now removed.
            variant_obj.featured_image = None
            variant_obj.save()

        return variant_obj


    class Meta:
        model = Variant
        exclude = ['is_active', 'created_at','product']
        # Product has been excluded but it will need to be passed as attribute while creating new variant


class ProductDetailsSerializer(serializers.ModelSerializer):
    class ProductOwnerSerializer(serializers.ModelSerializer):
        class Meta:
            model = SellerProfile
            fields = ['business_name', 'id']

    class ProductImageReadOnlySerializer(serializers.ModelSerializer):
        image = serializers.CharField(source = 'image_md.url') #Remove and replace uses with url

        url_md = serializers.SerializerMethodField()
        def get_url_md(self, image):
            return image.image_md.url

        url_lg = serializers.SerializerMethodField()
        def get_url_lg(self, image):
            return image.image_lg.url

        class Meta:
            model = ProductImage
            fields = ['id', 'image', 'url_md', 'url_lg']

    # variants = VariantSerializer(many=True)
    variants_data = serializers.SerializerMethodField('get_variants_data')
    owner = ProductOwnerSerializer(read_only=True)
    images = serializers.SerializerMethodField(read_only=True)
    tags = serializers.SerializerMethodField()
    vendors = serializers.SerializerMethodField()
    sub_categories = serializers.SerializerMethodField()
    is_favourite = serializers.SerializerMethodField()

    def get_is_favourite(self, product): 
        if 'request' in self.context:
            # requests will only be available is passed in extra context
            request = self.context['request']
            buyer_profile = request.user.buyer_profiles.first()
            return buyer_profile and buyer_profile.favourite_products.filter(id= product.id).exists()
        return None

    def get_tags(self,product):
        tags = product.tags.all()
        return TagsSerializer(tags,many=True).data
    
    def get_vendors(self,product):
        vendors = product.vendors
        return VendorsSerializer(vendors).data

    def get_sub_categories(self, product):
        sub_categories = product.sub_categories.all()
        return SubCategorySerializer2(sub_categories, many=True).data

    def get_images(self, product):
        qs = product.images.filter(is_active = True)
        serializer = self.ProductImageReadOnlySerializer(qs, many=True)
        return serializer.data

    

    def get_variants_data(self, instance):
        multiple = instance.has_multiple_variants()
        variants = instance.variants.filter(is_active=True) if multiple else instance.variants.filter(is_active=True).first()
        return {
            'multiple': multiple,
            'data': VariantSerializer(variants, many=multiple).data
        }
    
    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        print('\n\n\n\ internal Product value    -------->  ', data)

        variants_raw_data = data.get('variants_data')
        is_multi_variant = variants_raw_data.get('multiple')
        
        variant_options = variants_raw_data.get('options')
        variants_field_data = variants_raw_data.get('data')

        if is_multi_variant:
            for (fieldIndex, field_data) in enumerate(variants_field_data):
                for (optionIndex, option) in enumerate(variant_options, start=1):
                    field_data['option'+str(optionIndex)+'_name'] = option
                    # field_data['option'+str(optionIndex)+'_value'] = field_data['option'+str(optionIndex)]
                    # del field_data['option'+str(optionIndex)]
                variants_field_data[fieldIndex] = field_data
        
        else:
            variants_field_data['option1_name'] = 'default'
            variants_field_data['option1_value'] = 'default'

        variants_final_data = {
            'multiple': is_multi_variant,
            'data': variants_field_data
        }
        

        images = data.get('images')
        sub_categories = data.get('sub_categories')
        tags = data.get("tags",None)
        vendors = data.get("vendors",None)
        weight_unit = data.get("weight_unit")
        weight_value = get_wight_in_grams(data.get("weight_value"),weight_unit)
        # weight_value = float(data.get("weight_value")) / 1000 if weight_unit == "mg"  else (float(data.get("weight_value")) * 1000 if weight_unit == "kg" else float(data.get("weight_value")))
        country = data.get("country")
        allow_inventory_tracking = data.get("allow_inventory_tracking")
        allow_overselling = data.get("allow_overselling")

        internal_value.update({
            "allow_inventory_tracking":allow_inventory_tracking,
            "allow_overselling":allow_overselling,
            'variants_data': variants_final_data,
            'images': images,
            "weight_unit":weight_unit,
            "weight_value":weight_value,
            "tags":tags,
            "vendors":vendors,
            "country":country,
            'sub_categories': sub_categories,   #SerializerMethodField is readOnly. So need to include it here manually to save it
        })

        return internal_value

    @transaction.atomic
    def create(self, validated_data):
        print("\n\n\n validated Data ____________: ",validated_data)
        images = validated_data['images']
        del validated_data['images']    #Otherwise saving will break, as there are just image IDs in this field instead of instances
        tags_data = validated_data.pop("tags")
        variants_data = validated_data.pop('variants_data')
        seller = validated_data.get("owner")
        sub_categories = validated_data.pop("sub_categories")
        
        
        
        ######### Add or (Create then Add) tags in product #########
        
        tags = [(Tags.objects.create(name=tag.get("label"),seller=seller).id) if(tag.get("new")) else tag.get("id") for tag in list(tags_data)]
        
        ######### Add or (Create then Add) tags in product #########
        
        ######### Add or (Create then Add) vendors in product #########
        vendor_data = validated_data.pop("vendors")
        
        if vendor_data:
            vendor = Vendors.objects.create(name=vendor_data.get("label"),seller=seller) if(vendor_data.get("new")) else Vendors.objects.get(id=vendor_data.get("id"))
        
            validated_data["vendors"] = vendor
        ######### Add or (Create then Add) vendors in product #########

        product = Product.objects.create(**validated_data)
        
        product.tags.set(tags)
        
        product.sub_categories.set(sub_categories)
        
        is_multi_variant = variants_data['multiple']

        variants_serializer = VariantSerializer(data = variants_data['data'], many=is_multi_variant)
        if variants_serializer.is_valid(raise_exception=True):
            variants = variants_serializer.save(product = product)
        if images:
            image_order = 1
            for image_id in images:
                if image := ProductImage.objects.filter(id=image_id).first():
                    if image.uploaded_by != product.owner or image.product or not image.is_temp:
                        continue
                    initial_path = image.image.path
                    filename = os.path.split(initial_path)[1]
                    image.image.name = f'product_images/{product.id}/{filename}'
                    new_path = settings.MEDIA_ROOT + image.image.name
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))
                    os.rename(initial_path, new_path)
                    image.product = product
                    image.is_temp = False
                    image.order = image_order
                    image.save()
                    image_order += 1

                    image.generate_sizes()
                    
        ######### Sub categories start #########
        print("sub_categories type>>> ",type(sub_categories))
        sub_categories_initial = list(product.sub_categories.values_list("id",flat=True))
        sub_categories_remove = []
        categories = seller.operational_fields.filter(collection_type="automated")
        for category in categories:
            rule = get_auto_category_ORM_filters(category) 
            print("rule was >>>>> ",rule)
            if Product.objects.filter(id=product.id).filter(rule).exists():
                sub_categories_initial.append(category.id)
            else:
                sub_categories_remove.append(category.id)
                
        print(" \n\n\n sub_categories >>> ",sub_categories)
        product.sub_categories.set(sub_categories_initial)
        
        ######### Sub categories end #########

        return product
    
    @transaction.atomic
    def update(self, instance, validated_data):
        print(" \n\n\n\ update validated data is this >>>>>>>>>>> : ",validated_data)
        
        ######### Add or (Create then Add) tags in product #########
        seller = validated_data.get("owner")
        tags_data = validated_data.get("tags")
        del validated_data['tags']
                
        tags = [(Tags.objects.create(name=tag.get("label"),seller=seller).id) if(tag.get("new")) else tag.get("id") for tag in list(tags_data)]
                
        instance.tags.set(tags)
        
        
        ######### Add or (Create then Add) tags in product #########
        
        ######### Add or (Create then Add) vendors in product #########
        vendor_data = validated_data.pop("vendors")
        
        if vendor_data:
            vendor,created = Vendors.objects.get_or_create(name=vendor_data.get("label"),seller=seller)
            # vendor = Vendors.objects.create(name=vendor_data.get("label"),seller=seller) if(vendor_data.get("new")) else Vendors.objects.get(id=vendor_data.get("id"))
            
            validated_data["vendors"] = vendor
        ######### Add or (Create then Add) vendors in product #########
        
        ######### Add Sub categories in product #########
        
        sub_categories_add = validated_data.pop("sub_categories")
        sub_categories_remove = []
        categories = seller.operational_fields.filter(collection_type="automated")
        for category in categories:
            rule = get_auto_category_ORM_filters(category) 
            print("rule was >>>>> ",rule)
            if Product.objects.filter(id=instance.id).filter(rule).exists():
                sub_categories_add.append(category.id)
            else:
                sub_categories_remove.append(category.id) 
                 
        
        instance.sub_categories.set([sc for sc in sub_categories_add if sc not in sub_categories_remove])
        
        ######### Add Sub categories in product #########
        
        
        product = instance
        images = validated_data['images']
        del validated_data['images']    #Otherwise saving will break, as there are just image IDs in this field instead of instances
        images_before = set(instance.images.filter(is_active =True).values_list('id', flat=True))
        super().update(instance, validated_data)
        variants_data = validated_data['variants_data']
        is_multi_variant = variants_data['multiple']
        # print("VD", variants_data['data'])
        variants_before = set(product.variants.filter(is_active = True).values_list('id', flat=True))  
        variants_serializer = VariantSerializer(data = variants_data['data'], many=is_multi_variant)
        if variants_serializer.is_valid(raise_exception=True):
            variants = variants_serializer.save(product = product)
            print(f'{variants=}')
        variants_after = set(map(lambda v: v.id, variants)) if is_multi_variant else {variants.id}
        variants_to_be_removed = variants_before - variants_after
        Variant.objects.filter(id__in = variants_to_be_removed).update(is_active = False)
        print(f'{variants_before=}, {variants_after=}, diff={variants_before - variants_after}')

        if images:
            image_order = 1
            for image_id in images:
                if image := ProductImage.objects.filter(id=image_id).first():
                    if image.uploaded_by != product.owner or image.product or not image.is_temp:
                        if image.product == product: # If image is already attached to product. Other opterations below this block should already be completed if this is the case, hence 'continue'
                            image.order = image_order
                            image_order += 1
                            image.save()
                        continue
                    initial_path = image.image.path
                    filename = os.path.split(initial_path)[1]
                    image.image.name = f'product_images/{product.id}/{filename}'
                    new_path = settings.MEDIA_ROOT + image.image.name
                    if not os.path.exists(os.path.dirname(new_path)):
                        os.makedirs(os.path.dirname(new_path))
                    os.rename(initial_path, new_path)
                    image.product = product
                    image.is_temp = False
                    image.order = image_order
                    image.save()
                    image_order += 1

                    image.generate_sizes() 

        images_after = set(images)
        images_to_be_removed = images_before - images_after
        images_to_be_removed_queryset = ProductImage.objects.filter(id__in=images_to_be_removed)
        removed_images = images_to_be_removed_queryset.update(is_active =False)
        for image in images_to_be_removed_queryset:
            image.featured_in_variants.clear()  # Remove associated featured images

        return product

    class Meta:
        model = Product
        fields = ['id', 'title', 'slug', 'description', 'owner', 'images', 'variants_data',"vendors","tags", 'sub_categories', 'is_favourite',"weight_unit","weight_value","country","allow_inventory_tracking","allow_overselling"]
        # depth = 1


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = [
            # 'uploaded_by',
            'image',
            'id'
            ]
        read_only_fields = ['id']

class VariantDetailsSerializer(serializers.ModelSerializer):

    class ProductShortDetailsSerializer(serializers.ModelSerializer):
        seller_name = serializers.CharField(source='owner.business_name')
        class Meta:
            model = Product
            fields = ["id",'title',"slug", 'has_multiple_variants', 'id', 'seller_name',"allow_inventory_tracking","allow_overselling"]

    featured_image = serializers.SerializerMethodField()
    def get_featured_image(self, variant):
        if variant.featured_image:
            return variant.featured_image.image_md.url
        
        if product_image := variant.product.featured_image:
            return product_image.image_md.url
        
        return None

    # product_title = serializers.SerializerMethodField()
    # def get_product_title(self, variant):
    #     return variant.product.title

    product = ProductShortDetailsSerializer()

    class Meta:
        model = Variant
        exclude=['created_at']

class CategoriesSerializer2(serializers.ModelSerializer):
    
    sub_categories = serializers.SerializerMethodField()
    def get_sub_categories(self, category):
        try:
            sub_categories = category.sub_categories.filter(is_active=True).filter(Q(seller = self.context['request'].user.seller_profiles.first()))
        except:
            sub_categories = category.sub_categories.filter(is_active=True).filter(seller=None)
        return SubCategorySerializer(sub_categories, many=True).data
    
    seller = serializers.SerializerMethodField()
    def get_seller(self,category):
        name = None
        try:
            name = category.seller.owner.username
        except:
            name = None
        return name
    no_of_product = serializers.SerializerMethodField()
    def get_no_of_product(self,category):
        return category.products.filter(is_active=True).count()
    
    rules = serializers.SerializerMethodField()
    def get_rules(self,category):
        auto_category_rules = category.auto_category_rule.filter(is_active=True)
        return AutoCategoryRuleSerializer(auto_category_rules,many=True).data
        
    action = serializers.SerializerMethodField()
    def get_action(self,category):
        return category.collection_type
    
    condition = serializers.SerializerMethodField()
    def get_condition(self,category):
        return category.condition_type
    

    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            "description",
            "action",
            "condition",
            'seller',
            'sub_categories',
            'image',
            "no_of_product",
            "rules",
            "parent",
        ]
        extra_kwargs = {
            'image': {
                'required': False,
            },
        }
        # depth = 1

    def to_internal_value(self, data):
        value = super().to_internal_value(data)
        # print(" Validated data is this >>>>>>>>>>>>>>> ",data)
        
        # sub_categories_raw_data = json.loads(data['sub_categories'])
        # sub_categories_data = map(lambda sc: {_key: sc[_key] for _key in ['name', 'id',"seller"] if _key in sc}, sub_categories_raw_data) # By default, 'id' field for sub categories was omitted., hence needed to include it
        
        value["selectedProducts"] = json.loads(data["selectedProducts"])
        value["seller"] = data["seller"]
        action = data.get("action")
        condition = data.get("condition")
        rules = json.loads(data.get("rules"))
        description = data.get("description")
        
        # value['sub_categories'] = sub_categories_data # By default,  'id' field for sub categories was omitted.
        
        if 'delete_image' in data:
            value['delete_image'] = data['delete_image']
        value.update({
            "collection_type":action,
            "condition_type":condition if condition else None,
            "rules":list(rules) if rules else [],
            "description":description
        })
        
        return value

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.image:
            representation['image'] = instance.image_sm.url
        return representation

    def create(self, validated_data):
        # Not very secure, for staff use only. Will need to add more security if it needs to be open to public, like popping ID field
        
        # sub_categories_data = validated_data.pop('sub_categories')
        
        print("Category Data ----> ",validated_data)
        
        user = validated_data.pop("seller")
        selectedProducts = validated_data.pop("selectedProducts")
        # condition = validated_data.pop("condition")
        
        # print("Selecteds products is >>>>>>>>>>>>>>",type(selectedProducts))
        collection_type = validated_data.pop("collection_type")
        rules = validated_data.pop("rules")
        
        condition_type = validated_data.pop("condition_type")
        
        seller = User.objects.filter(username=user).first().seller_profiles.first()
        if collection_type == "automated":
            category = Category.objects.create(seller=seller,collection_type=collection_type,condition_type=condition_type,**validated_data)
            
            for rule in rules: 
                attribute_value = None
                if rule.get("attribute_name") == "weight":
                    attribute_value = get_wight_in_grams(float(rule.get("attribute_value")), rule.get("attribute_unit"))
                else:
                    attribute_value = rule.get("attribute_value")
                AutoCategoryRule.objects.create(category=category,attribute_name=rule.get("attribute_name"),comparison_type=rule.get("comparison_type"),attribute_value=attribute_value,attribute_unit=rule.get("attribute_unit",None))

            query = get_auto_category_ORM_filters(category)
            print(f"\n\n\n query is {query} \n\n\n")
            products = Product.objects.filter(owner=seller).filter(query)
            for product in products:
                product.sub_categories.add(category)

                # AutoCategoryRule.objects.create(category=category,**rule)
                
        elif collection_type == "manual":
            category = Category.objects.create(seller=seller,collection_type=collection_type,**validated_data)
            
            selected_products = Product.objects.filter(pk__in = selectedProducts, owner=seller, is_active = True)
            for selected_product in selected_products:
                selected_product.sub_categories.add(category)
                
        # if(category.parent):
        #     seller.operational_fields.add(category)
        # else:
        #     pass
        seller.operational_fields.add(category)
        
     
        # for sub_category in sub_categories_data:
        #     Category.objects.create(parent=category,seller=seller,**sub_category)

        return category

    def update(self, instance, validated_data):
        print(" \n\n\n Product Update is Called \n\n\n")
        user = User.objects.filter(username=validated_data.get("seller")).first()
        seller_profile = user.seller_profiles.first()
        # print("seller profile and category instance: ",instance,seller_profile)
        collection_type = validated_data.pop("collection_type")
        condition_type = validated_data.pop("condition_type",None)
        selectedProducts = validated_data.pop("selectedProducts")
        # parent = Category.objects.get(id=validated_data["parent"]) 
        
        if instance.seller == seller_profile:
            instance.name = validated_data['name']
            instance.description = validated_data["description"]
            instance.collection_type = collection_type
            instance.parent = validated_data["parent"]
            if collection_type == "automated":
                instance.condition_type = condition_type
            if 'delete_image' in validated_data:
                instance.image.delete(save=False)
            elif 'image' in validated_data:
                instance.image = validated_data['image']
            instance.save()
            
            
        if collection_type == "automated":
            auto_category_rule_initial = list(instance.auto_category_rule.all().values_list('id', flat=True))
            auto_category_rule_final = []
            rules_data = validated_data.pop("rules")
            # print("rules data----> ",rules_data)
            for rule_data in rules_data:
                if "id" in rule_data.keys():
                    rule = AutoCategoryRule(category=instance,**rule_data)
                else:
                    rule_data.pop("setFocus")
                    rule = AutoCategoryRule(category=instance,**rule_data)
                rule.save()
                auto_category_rule_final.append(rule.id)
                        
            rules_to_remove = [rule for rule in auto_category_rule_initial if rule not in auto_category_rule_final]
            AutoCategoryRule.objects.filter(id__in=rules_to_remove).update(is_active = False)
            
            query = get_auto_category_ORM_filters(instance)
            products = Product.objects.filter(query,owner=seller_profile)
            print("query products: ",products)
            
            category_product_initial = list(instance.products.filter(owner=seller_profile).values_list("id",flat=True))
            category_product_final = []
            for product in products:
                product.sub_categories.add(instance)
                category_product_final.append(product.id)
                
            category_product_to_remove = [sc for sc in category_product_initial if sc not in category_product_final]
            category_remove_products = Product.objects.filter(id__in=category_product_to_remove)
            for category_remove_product in category_remove_products:
                category_remove_product.sub_categories.remove(instance)

        # sub_categories_initial = list(instance.sub_categories.filter(Q(seller=None) | Q(seller=self.context['request'].user.seller_profiles.first())).values_list('id', flat=True))
        # print(sub_categories_initial)
        # sub_categories_final = []
        # sub_categories_data = validated_data.pop('sub_categories')
        # for sc_data in list(sub_categories_data):
        #     try:
        #         if "id" in sc_data.keys():
        #             user = User.objects.filter(username=sc_data.get("seller")).first()
        #             sc_data["seller"] = user.seller_profiles.first()
        #             print("sub-category updated")
        #         else:
        #             sc_data["seller"] = self.context['request'].user.seller_profiles.first()
        #             print("sub-category created")
        #     except:
        #         sc_data["seller"] = None
            
        #     print("sub-category updated",sc_data)
        #     sc = Category(parent=instance, **sc_data)
        #     sc.save()
        #     sub_categories_final.append(sc.id)
            
        # sub_categories_to_remove = [sc for sc in sub_categories_initial if sc not in sub_categories_final]
        # Category.objects.filter(id__in=sub_categories_to_remove).update(is_active = False)
        return instance

class SubCategorySerializer(serializers.ModelSerializer):
    seller = serializers.SerializerMethodField()
    def get_seller(self,category):
        name = None
        try:
            name = category.seller.owner.username
        except:
            name = None
        return name

    name = serializers.SerializerMethodField()
    def get_name(self,category):
        return category.name
    
    no_of_product = serializers.SerializerMethodField()
    def get_no_of_product(self,category):
        return category.products.filter(is_active=True).count()
    
    
    action = serializers.SerializerMethodField()
    def get_action(self,category):
        return category.collection_type
    
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            "seller",
            "no_of_product",
            "action"
        ]

class SubCategorySerializer2(serializers.ModelSerializer):
    category = serializers.SerializerMethodField()
    def get_category(self,category):
        parent = None
        try:
            parent = category.parent.name
        except:
            parent = "(Category)"
        return parent
     
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'category'
        ]

class AutoCategoryRuleSerializer(serializers.ModelSerializer):
    attribute_value = serializers.SerializerMethodField()
    def get_attribute_value(self,auto):
        if auto.attribute_name == "weight":
            return get_wight_in_grams(auto.attribute_value,auto.attribute_unit)
            # return float(auto.attribute_value) * 1000 if auto.attribute_unit == "mg" else float(auto.attribute_value) / 1000 if auto.attribute_unit == "kg" else auto.attribute_value
        return auto.attribute_value

    class Meta:
        model = AutoCategoryRule
        fields = ["id","attribute_name","attribute_value","comparison_type","attribute_unit"]

class TagsSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    def get_label(self,tags):
        return tags.name
    class Meta:
        model = Tags
        fields = ["id","label"]
        
class VendorsSerializer(serializers.ModelSerializer):
    
    label = serializers.SerializerMethodField()
    def get_label(self,vendors):
        return vendors.name
    class Meta:
        model = Vendors
        fields = ["id","label"]
        
        
class  BuyerSellerConnectionSerializers(serializers.ModelSerializer):
    
    buyer = serializers.SerializerMethodField()
    def get_buyer(self,connection):
        return {"id":connection.buyer.id,"name":connection.buyer.owner.name,"email":connection.buyer.owner.email,"business_name":connection.buyer.business_name}
    
    generic_discount = serializers.SerializerMethodField()
    def get_generic_discount(self,connection):
        discount = connection.buyer.buyer_discounts.filter(product=None,variant=None,is_active=True)
        if len(discount) > 0:
            return GenericDiscountSerializer(discount.first()).data
        return None
    
    product_discounts = serializers.SerializerMethodField()
    def get_product_discounts(self,connection):
        products = connection.buyer.buyer_discounts.filter(~Q(product=None) & Q(variant=None) & Q(is_active=True))
        return ExclusiveProductDiscountDetailSerializer(products,many=True).data

         
    class Meta:
        model = BuyerSellerConnection
        fields = ["id","buyer","generic_discount","product_discounts"] 
        
class SellerBuyerConnectionDetailSerializer(serializers.ModelSerializer):    
    buyer = serializers.SerializerMethodField()
    def get_buyer(self,connection):
        return connection.buyer.business_name
    
    seller = serializers.SerializerMethodField()
    def get_seller(self,connection):
        return connection.seller.business_name
    
    class Meta:
        model = BuyerSellerConnection
        fields = ["id","buyer","seller"]
        extra_kwargs = {"buyer":{"read_only":True},"seller":{"read_only":True}}
        
class BuyerAddressSerializer(serializers.ModelSerializer):
    state = ChoiceField(choices=BuyerAddress.STATE_CHOICES)
    class Meta:
        model = BuyerAddress
        fields = ["id","name","line1","line2","pin","city","state"]
        
class BuyerDetailSerializer(serializers.ModelSerializer):
    
    owner = serializers.SerializerMethodField()
    def get_owner(self,buyer):
        return buyer.owner.name
    
   
    address = serializers.SerializerMethodField()
    def get_address(self,buyer):
        print(self.context['request'].user)
        addresses = buyer.buyer_address.filter(is_active=True)
        return BuyerAddressSerializer(addresses,many=True).data
    
    global_discount = serializers.SerializerMethodField()
    def get_global_discount(self,buyer):
        discount = buyer.connections.filter(seller=self.context["request"].user.seller_profiles.first()).first().generic_discount
        print(discount)
        # generic_discount = buyer.connections.filter(seller=self.context["request"].user.id).first().generic_discount
        return discount
        
    
   
    
    class Meta:
        model = BuyerProfile
        fields = ["id","owner","business_name","address","global_discount"]
        
        
        
############### Buyer Discount Part Started ###############

class GenericDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDiscount
        fields = ["id","seller","buyer","discount_type","discount_value"]
        
class ExclusiveProductDiscountSerializer(serializers.ModelSerializer):
    class Meta:
        model = BuyerDiscount
        fields = ["id","seller","product","buyer","discount_type","discount_value"]
        
class ExclusiveProductDiscountDetailSerializer(serializers.ModelSerializer):
    class ProductShortDetailsSerializer(serializers.ModelSerializer):
        
        featured_image = serializers.SerializerMethodField()
        def get_featured_image(self, product):
            if product.featured_image:
                return product.featured_image.image_md.url
            return None
        
        class Meta:
            model = Product
            fields = ["id",'title',"featured_image"]
            
        
    product = ProductShortDetailsSerializer()
    
    class Meta:
        model = BuyerDiscount
        fields = ["id","product","buyer","seller","discount_type","discount_value"]
        
class BuyerDetailForDiscountSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    def get_name(self,buyer):
        return buyer.owner.name
    
    email = serializers.SerializerMethodField()
    def get_email(self,buyer):
        return buyer.owner.email
    
    generic_discount = serializers.SerializerMethodField()
    def get_generic_discount(self,buyer):
        discount = buyer.buyer_discounts.filter(product=None,variant=None,is_active=True)
        if len(discount) > 0:
            return GenericDiscountSerializer(discount.first()).data
        return None
    
    product_discounts = serializers.SerializerMethodField()
    def get_product_discounts(self,buyer):
        products = buyer.buyer_discounts.filter(~Q(product=None) & Q(variant=None) & Q(is_active=True))
        return ExclusiveProductDiscountDetailSerializer(products,many=True).data
    
    address = serializers.SerializerMethodField()
    def get_address(self,buyer):
        addresses = buyer.buyer_address.filter(is_active=True)
        return BuyerAddressSerializer(addresses,many=True).data
    
    class Meta:
        model = BuyerProfile
        fields = ["id","name","email","business_name","address","generic_discount","product_discounts"]
        
############### Buyer Discount Part End ###############

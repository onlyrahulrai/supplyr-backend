import os
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Product, Variant, ProductImage
from supplyr.core.models import Profile
from django.conf import settings

class ProductListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ['id', 'title', 'featured_image', 'price', 'sale_price', 'has_multiple_variants', 'quantity']


    featured_image = serializers.SerializerMethodField()
    def get_featured_image(self, instance):
        if image := instance.featured_image:
            return image.url
        return None

    price = serializers.SerializerMethodField()
    def get_price(self, instance):
        return instance.default_variant.price

    sale_price = serializers.SerializerMethodField()
    def get_sale_price(self, instance):
        return instance.default_variant.sale_price or instance.default_variant.price

    quantity = serializers.SerializerMethodField()
    def get_quantity(self, instance):
        return instance.default_variant.quantity or instance.default_variant.quantity

        

class VariantSerializer(serializers.ModelSerializer):

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
        if id := data.get('id'):
            internal_value['id'] = id
        return internal_value

    def create(self, validated_data):
        print ("vdata", validated_data)
        if id := validated_data.get('id'):
            if variant := Variant.objects.get(id=id, product=validated_data.get('product')):
                return self.update(variant, validated_data)

        return super().create(validated_data)


    class Meta:
        model = Variant
        exclude = ['is_active', 'created_at','product']
        # Product has been excluded but it will need to be passed as attribute while creating new variant



class ProductDetailsSerializer(serializers.ModelSerializer):
    class ProductOwnerSerializer(serializers.ModelSerializer):
        class Meta:
            model = Profile
            fields = ['business_name', 'id']

    class ProductImagesSerializer(serializers.ModelSerializer):
        image = serializers.CharField(source = 'image_md.url')
        
        class Meta:
            model = ProductImage
            fields = ['id', 'image']

    # variants = VariantSerializer(many=True)
    variants_data = serializers.SerializerMethodField('get_variants_data')
    owner = ProductOwnerSerializer(read_only=True)
    images = ProductImagesSerializer(read_only=True, many=True)


    def get_variants_data(self, instance):
        multiple = instance.has_multiple_variants()
        variants = instance.variants.filter(is_active=True) if multiple else instance.variants.filter(is_active=True).first()
        return {
            'multiple': multiple,
            'data': VariantSerializer(variants, many=multiple).data
        }
    
    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)
        # print('internal_value', data)

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

        internal_value.update({
            'variants_data': variants_final_data,
            'images': images,
        })

        return internal_value

    def create(self, validated_data):
        product = Product.objects.create(title=validated_data['title'], description=validated_data.get('description'), owner=validated_data['owner'])
        variants_data = validated_data['variants_data']
        is_multi_variant = variants_data['multiple']

        variants_serializer = VariantSerializer(data = variants_data['data'], many=is_multi_variant)
        if variants_serializer.is_valid(raise_exception=True):
            variants = variants_serializer.save(product = product)

        if validated_data['images']:
            for image_id in validated_data['images']:
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
                    image.save()

                    image.generate_sizes()


        print("Project", product, "variants", product.variants.all())
        print("VD", validated_data)
        return product
    
    def update(self, instance, validated_data):
        product = instance
        super().update(instance, validated_data)
        variants_data = validated_data['variants_data']
        is_multi_variant = variants_data['multiple']
        print("VD", variants_data['data'])
        variants_before = set(product.variants.filter(is_active = True).values_list('id', flat=True))  
        variants_serializer = VariantSerializer(data = variants_data['data'], many=is_multi_variant)
        if variants_serializer.is_valid(raise_exception=True):
            variants = variants_serializer.save(product = product)
            print(f'{variants=}')
        variants_after = set(map(lambda v: v.id, variants))
        variants_to_be_removed = variants_before - variants_after
        Variant.objects.filter(id__in = variants_to_be_removed).update(is_active = False)
        print(f'{variants_before=}, {variants_after=}, diff={variants_before - variants_after}')

        # if validated_data['images']:
        #     for image_id in validated_data['images']:
        #         if image := ProductImage.objects.filter(id=image_id).first():
        #             if image.uploaded_by != product.owner or image.product or not image.is_temp:
        #                 continue
        #             initial_path = image.image.path
        #             filename = os.path.split(initial_path)[1]
        #             image.image.name = f'product_images/{product.id}/{filename}'
        #             new_path = settings.MEDIA_ROOT + image.image.name
        #             if not os.path.exists(os.path.dirname(new_path)):
        #                 os.makedirs(os.path.dirname(new_path))
        #             os.rename(initial_path, new_path)
        #             image.product = product
        #             image.is_temp = False
        #             image.save()

        #             image.generate_sizes()

        return product

    class Meta:
        model = Product
        fields = ['id', 'title', 'description', 'owner', 'images', 'variants_data']
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
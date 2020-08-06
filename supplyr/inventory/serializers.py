from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import Product, Variant

class VariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Variant
        exclude = ['is_active', 'created_at','product']

class ProductDetailsSerializer(serializers.ModelSerializer):
    # variants = VariantSerializer(many=True)
    variants_data = serializers.SerializerMethodField('get_variants_data')


    def get_variants_data(self, instance):
        multiple = instance.has_mutiple_variants()
        variants = instance.variants if multiple else instance.variants.first()
        return {
            'multiple': multiple,
            'data': VariantSerializer(variants, many=multiple).data
        }
    
    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        variants_raw_data = data.get('variants_data')
        is_multi_variant = variants_raw_data.get('multiple')
        
        variant_options = variants_raw_data.get('options')
        variants_field_data = variants_raw_data.get('data')

        if is_multi_variant:
            for (fieldIndex, field_data) in enumerate(variants_field_data):
                for (optionIndex, option) in enumerate(variant_options, start=1):
                    field_data['option'+str(optionIndex)+'_name'] = option
                    field_data['option'+str(optionIndex)+'_value'] = field_data['option'+str(optionIndex)]
                    del field_data['option'+str(optionIndex)]
                variants_field_data[fieldIndex] = field_data
        
        else:
            variants_field_data['option1_name'] = 'default'
            variants_field_data['option1_value'] = 'default'

        variants_final_data = {
            'multiple': is_multi_variant,
            'data': variants_field_data
        }

        internal_value.update({
            'variants_data': variants_final_data
        })

        return internal_value

    def create(self, validated_data):
        product = Product.objects.create(title=validated_data['title'], description=validated_data['description'], owner=validated_data['owner'])
        variants_data = validated_data['variants_data']

        variants_serializer = VariantSerializer(data = variants_data['data'], many=variants_data['multiple'])
        if variants_serializer.is_valid(raise_exception=True):
            variants = variants_serializer.save(product = product)

        print("Project", product, "variants", product.variants.all())
        return product
        


    class Meta:
        model = Product
        fields = ['title', 'description', 'variants_data']
        depth = 1
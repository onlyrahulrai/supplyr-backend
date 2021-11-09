import os
from PIL import Image
from django.core.files.base import ContentFile
from io import BytesIO
from django.db.models import Q


def generate_image_sizes(instance, field_name, schema, save = True):
    print("GENERATING SCHEMA")
    image_field = getattr(instance, field_name)
    
    original_image = Image.open(image_field)
    ext = os.path.splitext(image_field.path)[1]

    if ext in [".jpg", ".jpeg"]:
        PIL_TYPE = 'JPEG'
        FILE_EXTENSION = 'jpg'

    elif ext == ".png":
        PIL_TYPE = 'PNG'
        FILE_EXTENSION = 'png'

    if original_image.mode not in ('L', 'RGB'):
        original_image = original_image.convert('RGB')

    for image_variant in schema:
        field = getattr(instance, image_variant['field_name'])
        new_image = original_image.copy()
        new_image.thumbnail(image_variant['size'], Image.ANTIALIAS)
        fp = BytesIO()
        new_image.save(fp, PIL_TYPE, quality=image_variant['quality'])
        cf = ContentFile(fp.getvalue())
        field.save('only_ext_is_relevant.' + FILE_EXTENSION, content = cf, save = False)

    if save:
        instance.save()
    # return instance # Not really needed, the instance will get updated through reference
    


def get_orm_filter_from_rule(rule):
    product_attribute_keys = {
        "product_title":"title",
        "product_vendor":"vendors__name",
        "product_category":"sub_categories__name",
        "product_tag":"tags__name",
        "compare_at_price":"variants__price",
        "inventory_stock":"variants__quantity",
        "weight":"weight_value",
        "variants_title":"variants__product__title"
    }
    query = None
    if rule.attribute_name in ["product_title","product_category","product_vendor","product_tag","compare_at_price","inventory_stock","weight","variants_title"]:
        if rule.comparison_type == "is_not_equal_to":
            query = ~Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}":rule.attribute_value})
        elif rule.comparison_type == "is_greater_than":
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}__gt":rule.attribute_value})
        elif rule.comparison_type == "is_less_than":
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}__lt":rule.attribute_value})
        elif rule.comparison_type == "contains":
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}__icontains":rule.attribute_value})
        elif rule.comparison_type == "starts_with":
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}__startswith":rule.attribute_value})
        elif rule.comparison_type == "ends_with":
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}__endswith":rule.attribute_value})
        else:
            query = Q(**{f"{product_attribute_keys.get(rule.attribute_name,None)}":rule.attribute_value})
    else:
        pass
    
    return query


def get_auto_category_ORM_filters(category):
    auto_category_rules = category.auto_category_rule.filter(is_active=True)
    query = Q()
    for auto_category_rule in auto_category_rules:
        orm_filter = get_orm_filter_from_rule(auto_category_rule)
        if category.condition_type  == "all":
            query &= orm_filter
        else:
            query |= orm_filter
            
    return query

def get_wight_in_grams(weight_value, weight_unit):
    return float(weight_value or 0) / 1000 if weight_unit == "mg" else (float(weight_value or 0) * 1000 if weight_unit == "kg" else float(weight_value or 0))
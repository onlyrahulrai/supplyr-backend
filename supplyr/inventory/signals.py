from django.db.models import query
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile

from supplyr.core.model_utils import get_auto_category_ORM_filters
from .models import Category, Product, ProductImage
from PIL import Image
from io import BytesIO
from supplyr.profiles.models import SellerProfile

@receiver(post_save, sender=ProductImage)
def generate_thumbnail(sender, instance, created, **kwargs):
    print("Came in signal ", instance, created)
    # if isntance.is_default == True:

    if created:
        # instance.generate_sizes()
        pass
    
@receiver(post_save,sender=Product)
def auto_category_rule_create(sender,instance,**kwargs):
    if instance.id is not None:
        current = instance
        product = Product.objects.get(id=current.id)
        seller = SellerProfile.objects.get(id=current.owner.id)
        categories =  seller.operational_fields.filter(collection_type="automated")
        for category in categories:
            rule = get_auto_category_ORM_filters(category)
            if Product.objects.filter(id=current.id).filter(rule).exists():
                product.sub_categories.add(category)
            else:
                product.sub_categories.remove(category)
            
            

    
        

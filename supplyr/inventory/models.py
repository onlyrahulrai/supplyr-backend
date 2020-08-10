from datetime import datetime
import os
from django.db import models
from django.contrib.auth import get_user_model

from django_mysql.models import Model

User = get_user_model()

class Product(Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('core.Profile', related_name='products', on_delete=models.CASCADE)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def has_mutiple_variants(self):
        if self.variants.count() > 1:
            return True
        elif variant := self.variants.first():
            return not (variant.option1_name == "default" and variant.option1_value == "default")
        
        return False
    

class Variant(Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')

    option1_name = models.CharField(max_length=30, blank=True, null=True)
    option1_value = models.CharField(max_length=50, blank=True, null=True)

    option2_name = models.CharField(max_length=30, blank=True, null=True)
    option2_value = models.CharField(max_length=30, blank=True, null=True)

    option3_name = models.CharField(max_length=50, blank=True, null=True)
    option3_value = models.CharField(max_length=50, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    sale_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductImage(Model):
    def get_image_upload_path(self, filename, thumb=False):
        file, ext = os.path.splitext(filename)
        new_filename = 'product_temp_images/' + str(int(datetime.now().timestamp())) + ('_thumb' if thumb else '') + ext
        #Default temporary upload path. It will be relocated once product in saved
        return new_filename

    def get_thumb_upload_path(self, filename):
        return get_image_upload_path(self, filename, True)

    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name='images')
    image = models.ImageField(upload_to = get_image_upload_path)
    thumbnail = models.ImageField(upload_to= get_thumb_upload_path, blank=True, null=True)
    serial = models.PositiveSmallIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('core.Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_temp = models.BooleanField(default=True)





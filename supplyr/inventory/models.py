import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django_mysql.models import Model
from PIL import Image
from supplyr.core.model_utils import generate_image_sizes

User = get_user_model()


class Product(Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('core.Profile', related_name='products', on_delete=models.CASCADE)
    sub_categories = models.ManyToManyField('core.SubCategory', related_name='products')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def has_multiple_variants(self):
        if self.variants.filter(is_active=True).count() > 1:
            return True
        elif variant := self.variants.filter(is_active=True).first():
            return not (variant.option1_name == "default" and variant.option1_value == "default")
        
        return False

    @property
    def featured_image(self):
        if image := self.images.first():
            if image_sm := image.image_sm:
                return image_sm
        return None

    @property
    def default_variant(self):
        return self.variants.first()
    

class Variant(Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')

    option1_name = models.CharField(max_length=50, blank=True, null=True)
    option1_value = models.CharField(max_length=150, blank=True, null=True)

    option2_name = models.CharField(max_length=50, blank=True, null=True)
    option2_value = models.CharField(max_length=150, blank=True, null=True)

    option3_name = models.CharField(max_length=50, blank=True, null=True)
    option3_value = models.CharField(max_length=150, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    sale_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    featured_image = models.ForeignKey('ProductImage', blank=True, null=True, on_delete=models.SET_NULL, related_name='featured_in_variants')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ProductImage(Model):

    image_sizes = [
        {
            'field_name': 'image_sm',
            'size': [200,200],
            'quality': 60,
        },
        {
            'field_name': 'image_md',
            'size': [800,800],
            'quality': 70,
        },
    ]

    def get_image_upload_path(self, filename, size = None):
        file, ext = os.path.splitext(filename)
        if self.product:
            base_directory = os.path.join('product_images', str(self.product.id))
        else:
            base_directory = 'product_temp_images'
        new_filename = os.path.join(base_directory, str(int(datetime.now().timestamp())) + (('_'+ size) if size else '') + ext)
        return new_filename

    def get_image_sm_upload_path(self, filename):
        return self.get_image_upload_path(filename, size="sm")
    def get_image_md_upload_path(self, filename):
        return self.get_image_upload_path(filename, size="md")
    

    product = models.ForeignKey(Product, on_delete=models.CASCADE, blank=True, null=True, related_name='images')
    image = models.ImageField(upload_to = get_image_upload_path)
    image_sm = models.ImageField(upload_to= get_image_sm_upload_path, blank=True, null=True)
    image_md = models.ImageField(upload_to= get_image_md_upload_path, blank=True, null=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('core.Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_temp = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def generate_sizes(self):
        generate_image_sizes(self, 'image', self.image_sizes)

    
    class Meta:
        ordering = ['order']


from .signals import *
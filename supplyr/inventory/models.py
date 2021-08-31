import os
from datetime import datetime
from io import BytesIO

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import models
from django.db.models.enums import Choices
from django.template.defaultfilters import default, slugify
from django_mysql.models import Model
from PIL import Image
from supplyr.core.model_utils import generate_image_sizes
from django.utils.functional import cached_property
from django_extensions.db.fields import AutoSlugField
from django_mysql.models import EnumField

User = get_user_model()

class Search(models.Lookup):
   lookup_name = 'search'

   def as_mysql(self, compiler, connection):
       lhs, lhs_params = self.process_lhs(compiler, connection)
       rhs, rhs_params = self.process_rhs(compiler, connection)
       params = lhs_params + rhs_params
       return 'MATCH (%s) AGAINST (%s IN BOOLEAN MODE)' % (lhs, rhs), params

models.CharField.register_lookup(Search)
models.TextField.register_lookup(Search)


class Category(models.Model):
    image_sizes = [
        {
            'field_name': 'image_sm',
            'size': [200,200],
            'quality': 60,
        },
    ]

    def get_image_upload_path(self, filename, size = None):
        file, ext = os.path.splitext(filename)
        base_directory = 'category-images'
        new_filename = os.path.join(base_directory, str(self.id or slugify(self.name)) + (('_'+ size) if size else '') + ext)
        return new_filename

    def get_image_sm_upload_path(self, filename):
        return self.get_image_upload_path(filename, size="sm")
    

    name = models.CharField(max_length=50)
    serial = models.PositiveSmallIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to=get_image_upload_path, blank=True, null=True)
    image_sm = models.ImageField(upload_to=get_image_sm_upload_path, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, related_name="sub_categories",null=True,blank=True)
    seller = models.ForeignKey('profiles.SellerProfile', on_delete=models.CASCADE,null=True,blank=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._existing_image = self.image

    def __str__(self):
        return f'[{self.id}] {self.name}'

    def save(self, *args, **kwargs):
        if self.image != self._existing_image or (self.image and not self.id): #image is changed, or it's a new category
            generate_image_sizes(self, 'image', self.image_sizes, save = False) # Save is omitted here to prevent recursion
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['serial']
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'

class Tags(models.Model):
    name = models.CharField(max_length=200)
    seller = models.ForeignKey('profiles.SellerProfile',on_delete=models.CASCADE,related_name="tags")
    created_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        
    def __str__(self):
        return f'[{self.id}] {self.name}'
    
class Vendors(models.Model):
    name = models.CharField(max_length=200)
    seller = models.ForeignKey('profiles.SellerProfile',on_delete=models.CASCADE,related_name="vendors")
    created_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'
        
    def __str__(self):
        return f'[{self.id}] {self.name}'

class Product(Model):
    class WeightUnit(models.TextChoices):
        MG = 'mg', 'Milligram'
        GM = 'gm', 'Gram'
        KG = 'kg', 'Kilogram'
        lb = 'lbs', 'lbs'
        
    title = models.CharField(max_length=200)
    slug = AutoSlugField(max_length=100, populate_from=['title'], unique=True)
    description = models.TextField(blank=True, null=True)
    owner = models.ForeignKey('profiles.SellerProfile', related_name='products', on_delete=models.CASCADE)
    vendors = models.ForeignKey('inventory.vendors', related_name='products', on_delete=models.CASCADE,blank=True,null=True)
    sub_categories = models.ManyToManyField('inventory.Category', related_name='products')
    tags = models.ManyToManyField('inventory.Tags', related_name='products')
    weight_unit = EnumField(choices=WeightUnit.choices,blank=True,null=True)
    weight_value = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    @property
    def weight(self):
        return f'{self.weight_value}{self.weight_unit}'

    def has_multiple_variants(self):
        if self.variants_count > 1:
            return True
        elif default_variant := self.default_variant:
            #  variant = self.variants.filter(is_active=True).first():   # This is not using prefetched value becaused django is applying is_active twice and treating it as distinct query
            return not (default_variant.option1_name == "default" and default_variant.option1_value == "default")
        
        return False

    def __str__(self):
        return f'[{self.id}] {self.title[:20]}'

    @cached_property
    def variants_count(self):
        if hasattr(self, 'variants_count_annotated'):
            return self.variants_count_annotated
        return self.variants.filter(is_active=True).count()

    @property
    def featured_image(self):
        if hasattr(self, 'active_images_prefetched'):
            image = (len(self.active_images_prefetched) > 0) and self.active_images_prefetched[0]
        else:
            image = self.images.filter(is_active = True).first()
        if image:
            return image
            # if image_sm := image.image_sm:
            #     return image_sm
        return None

    @cached_property
    def default_variant(self):
        if hasattr(self, 'active_variants_prefetched'):
            return (len(self.active_variants_prefetched) > 0) and self.active_variants_prefetched[0]
        return self.variants.filter(is_active=True).first()
    

class Variant(Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')

    option1_name = models.CharField(max_length=50, blank=True, null=True)
    option1_value = models.CharField(max_length=150, blank=True, null=True)

    option2_name = models.CharField(max_length=50, blank=True, null=True)
    option2_value = models.CharField(max_length=150, blank=True, null=True)

    option3_name = models.CharField(max_length=50, blank=True, null=True)
    option3_value = models.CharField(max_length=150, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)
    minimum_order_quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    actual_price = models.DecimalField(decimal_places=2, max_digits=12, blank=True, null=True)
    featured_image = models.ForeignKey('ProductImage', blank=True, null=True, on_delete=models.SET_NULL, related_name='featured_in_variants')

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('id',)


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
        {
            'field_name': 'image_lg',
            'size': [1200,1200],
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
    image_lg = models.ImageField(upload_to= get_image_md_upload_path, blank=True, null=True)
    order = models.PositiveSmallIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('profiles.SellerProfile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_temp = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    def generate_sizes(self):
        generate_image_sizes(self, 'image', self.image_sizes)

    
    class Meta:
        ordering = ['order']


from .signals import *
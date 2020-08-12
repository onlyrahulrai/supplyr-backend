from datetime import datetime
import os
from django.db import models
from django.contrib.auth import get_user_model

from django_mysql.models import Model
from django.core.files.base import ContentFile
from PIL import Image
from io import BytesIO

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
    serial = models.PositiveSmallIntegerField(blank=True, null=True)
    uploaded_by = models.ForeignKey('core.Profile', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_temp = models.BooleanField(default=True)

    def generate_sizes(self):
        original_image = Image.open(self.image)
        ext = os.path.splitext(self.image.path)[1]

        if ext in [".jpg", ".jpeg"]:
            PIL_TYPE = 'JPEG'
            FILE_EXTENSION = 'jpg'

        elif ext == ".png":
            PIL_TYPE = 'PNG'
            FILE_EXTENSION = 'png'

        if original_image.mode not in ('L', 'RGB'):
            original_image = original_image.convert('RGB')

        for image in self.image_sizes:
            if not (field := getattr(self, image['field_name'])):
                new_image = original_image.copy()
                new_image.thumbnail(image['size'], Image.ANTIALIAS)
                fp = BytesIO()
                new_image.save(fp, PIL_TYPE, quality=image['quality'])
                cf = ContentFile(fp.getvalue())
                field.save('only_ext_is_relevant.' + FILE_EXTENSION, content = cf, save = False)

        self.save()





from .signals import *
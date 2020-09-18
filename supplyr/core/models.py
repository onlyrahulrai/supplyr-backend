import os
from django.db import models
from django.contrib.auth.models import AbstractUser
from os.path import splitext
from django_mysql.models import Model
from django_mysql.models import EnumField
from supplyr.core.model_utils import generate_image_sizes

class User(AbstractUser):

    BUYER_GROUP_NAME = 'buyer'
    SELLER_GROUP_NAME = 'seller'
    
    @property
    def name(self):
        return self.first_name

    @name.setter
    def name(self, value):
        self.first_name = value
        self.save()

    @property
    def status(self):
        if self.seller_profiles.filter(is_approved=True).exists():
            return 'approved'
        elif self.seller_profiles.exclude(operational_fields = None).exists():
            return 'categories_selected'
        elif self.seller_profiles.exists():
            return 'form_filled'
        else:
            return 'verified'

    @property
    def is_approved(self):
        return self.status == 'approved'

    @property
    def is_buyer(self):
        return self.groups.filter(name=self.BUYER_GROUP_NAME).exists()
    
    @property
    def is_seller(self):
        return self.groups.filter(name=self.SELLER_GROUP_NAME).exists()
    

    # @property
    # def status_int(self):
    #     return 3

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
        new_filename = os.path.join(base_directory, str(self.id) + (('_'+ size) if size else '') + ext)
        return new_filename

    def get_image_sm_upload_path(self, filename):
        return self.get_image_upload_path(filename, size="sm")
    

    name = models.CharField(max_length=50)
    serial = models.PositiveSmallIntegerField(null=True, blank=True)
    image = models.ImageField(upload_to=get_image_upload_path, blank=True, null=True)
    image_sm = models.ImageField(upload_to=get_image_sm_upload_path, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._existing_image = self.image

    def save(self, *args, **kwargs):
        if self.image != self._existing_image:
            generate_image_sizes(self, 'image', self.image_sizes, save = False) # Save is omitted here to prevent recursion
        return super().save(*args, **kwargs)

    class Meta:
        ordering = ['serial']

class SubCategory(models.Model):
    name = models.CharField(max_length=50)
    serial = models.PositiveSmallIntegerField(null= True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_categories')
    is_active = models.BooleanField(default=True)

def get_document_upload_path(instance, filename, document_category):
    file, ext = splitext(filename)
    new_filename = document_category + ext
    return f"documents/{ instance.id }/{ new_filename }"

def get_gst_upload_path(instance, filename):
    return get_document_upload_path(instance, filename, 'gst')

class SellerProfile(Model):
    class EntityTypes(models.TextChoices):
        PVTLTD = 'pvtltd', 'Private Limited'
        LLP = 'llp', 'Limited Liablity Partnership'
        PARTNER = 'part', 'Partnership'
        PROPRIETERSHIP = 'prop', 'Propertieship'

    class EntityCategory(models.TextChoices):
        MANUFACTURER = 'M', 'Manufacturer'
        DISTRIBUTOR = 'D', 'Distributer'
        WHOLESELLER = 'W', 'Wholeseller'


    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='seller_profiles')
    business_name = models.CharField(max_length=100, blank=True, null=True)
    entity_category = EnumField(choices=EntityCategory.choices, blank=True, null=True) 
    entity_type = EnumField(choices=EntityTypes.choices, blank=True, null=True)
    is_gst_enrolled = models.BooleanField(default=False, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=15, blank=True, null=True)
    tan_number = models.CharField(max_length=15, blank=True, null=True)
    gst_certificate = models.FileField(upload_to=get_gst_upload_path, max_length=150, blank=True, null=True)
    operational_fields = models.ManyToManyField(SubCategory, blank=True)
    is_approved = models.BooleanField(default=False)


    class Meta:
        verbose_name_plural = 'Seller Profiles'

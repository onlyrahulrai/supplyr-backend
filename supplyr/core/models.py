from django.db import models
from django.contrib.auth.models import AbstractUser
from os.path import splitext
from django_mysql.models import Model
from django_mysql.models import EnumField


class User(AbstractUser):
    
    @property
    def name(self):
        return self.first_name

    @name.setter
    def name(self, value):
        self.first_name = value
        self.save()

    @property
    def status(self):
        if self.profiles.filter(is_approved=True).exists():
            return 'approved'
        elif self.profiles.exclude(operational_fields = None).exists():
            return 'categories_selected'
        elif self.profiles.exists():
            return 'form_filled'
        else:
            return 'verified'

    # @property
    # def status_int(self):
    #     return 3

class Category(models.Model):
    name = models.CharField(max_length=50)
    serial = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['serial']

class SubCategory(models.Model):
    name = models.CharField(max_length=50)
    serial = models.PositiveSmallIntegerField(null= True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_categories')
    is_active = models.BooleanField(default=True)

def get_document_upload_path(instance, filename, document_category):
    file, ext = splitext(filename)
    new_filename = 'gst' + ext
    return f"documents/{ instance.id }/{ new_filename }"

class Profile(Model):
    class EntityTypes(models.TextChoices):
        PVTLTD = 'pvtltd', 'Private Limited'
        LLP = 'llp', 'Limited Liablity Partnership'
        PARTNER = 'part', 'Partnership'
        PROPRIETERSHIP = 'prop', 'Propertieship'

    class EntityCategory(models.TextChoices):
        MANUFACTURER = 'M', 'Manufacturer'
        DISTRIBUTOR = 'D', 'Distributer'
        WHOLESELLER = 'W', 'Wholeseller'

    def get_gst_upload_path(self, filename):
        return get_document_upload_path(self, filename, 'gst')

    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
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
        verbose_name_plural = 'Profiles'



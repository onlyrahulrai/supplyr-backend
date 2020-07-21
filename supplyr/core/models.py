from django.db import models
from django.contrib.auth.models import AbstractUser


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
        return 'verified'


class Entity(models.Model):
    class EntityTypes(models.TextChoices):
        PVTLTD = 'pvtltd', 'Private Limited'
        LLP = 'llp', 'Limited Liablity Partnership'
        PARTNER = 'part', 'Partnership'
        PROPRIETERSHIP = 'prop', 'Propertieship'

    class EntityCategory(models.IntegerChoices):
        MANUFACTURER = 1, 'Manufacturer'
        DISTRIBUTOR = 2, 'Distributer'
        WHOLESELLER = 3, 'Wholeseller'

    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    business_name = models.CharField(max_length=100)
    entity_category = models.IntegerField(choices=EntityCategory.choices)
    entity_type = models.CharField(max_length=15, choices=EntityTypes.choices)
    is_gst_enrolled = models.BooleanField(default=False, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=15, blank=True, null=True)
    tan_number = models.CharField(max_length=15, blank=True, null=True)


    class Meta:
        verbose_name_plural = 'Entities'

    
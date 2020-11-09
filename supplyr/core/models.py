import os
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from os.path import splitext
from django_mysql.models import Model
from django_mysql.models import EnumField
from django.utils.functional import cached_property
from supplyr.core.model_utils import generate_image_sizes
from django.utils.crypto import get_random_string
import string
import random

class User(AbstractUser):

    mobile_number = models.CharField(max_length=14)

    BUYER_GROUP_NAME = 'buyer'
    SELLER_GROUP_NAME = 'seller'
    
    @property
    def name(self):
        return F"{self.first_name} {self.last_name}"

    # @name.setter
    # def name(self, value):
    #     self.first_name = value
    #     self.save()

    @property
    def seller_status(self):
        if self.seller_profiles.filter(is_approved=True).exists():
            return 'approved'
        elif self.seller_profiles.exclude(operational_fields = None).exists():
            return 'categories_selected'
        elif self.seller_profiles.exists():
            return 'form_filled'
        else:
            return 'verified'

    @property
    def buyer_status(self):
        if self.buyer_profiles.exists():
            return 'ready'
        else:
            return 'verified'

    @cached_property
    def is_approved(self):
        return self.seller_status == 'approved'

    @property
    def is_buyer(self):
        return self.groups.filter(name=self.BUYER_GROUP_NAME).exists()

    def add_to_buyers_group(self):
        buyer_group = Group.objects.filter(name = self.BUYER_GROUP_NAME).first()
        if buyer_group:
            self.groups.add(buyer_group)

    def get_buyer_profile(self):
        return self.buyer_profiles.first()
            
    
    @property
    def is_seller(self):
        return self.groups.filter(name=self.SELLER_GROUP_NAME).exists()
    

    # @property
    # def status_int(self):
    #     return 3



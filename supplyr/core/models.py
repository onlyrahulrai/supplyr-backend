import os
import re
from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from os.path import splitext
from django_mysql.models import Model
from django_mysql.models import EnumField
from django.utils.functional import cached_property
from supplyr.core.model_utils import generate_image_sizes
from supplyr.utils.otp import send_otp, generate_otp
from django.utils.crypto import get_random_string
from allauth.account.models import EmailAddress
import string
import random

class User(AbstractUser):

    mobile_number = models.CharField(max_length=14)
    is_mobile_verified = models.BooleanField(default=False)

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
        elif self.is_email_verified and self.is_mobile_verified:
            return 'verified' # unprofiled
        else:
            return 'unverified'

    @property
    def buyer_status(self):
        if not all([self.is_email_verified, self.is_mobile_verified]):
            return 'unverified'
        if self.buyer_profiles.exists():
            return 'ready'
        else:
            return 'unprofiled'

    @property
    def salesperson_status(self):
        if self.salesperson_profiles.exists():
            return 'ready'
        return None

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

    def get_seller_profile(self):
        return self.seller_profiles.first()

    def get_sales_profile(self):
        return self.salesperson_profiles.first()

    @property
    def is_email_verified(self):
        return EmailAddress.objects.filter(user_id=self.id, verified=True).exists()

            
    
    @property
    def is_seller(self):
        return self.groups.filter(name=self.SELLER_GROUP_NAME).exists()
    

    # @property
    # def status_int(self):
    #     return 3


class MobileVerificationOTP(models.Model):
    code = models.CharField(max_length=10, default=generate_otp)
    user = models.ForeignKey(User, on_delete = models.CASCADE, related_name = 'verification_otps')
    mobile_number = models.CharField(max_length=14)
    # otp_id = models.CharField(max_length=128, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    send_count = models.SmallIntegerField(default=0)
    # is_expired = models.BooleanField(default=False)
    # is_verified = models.BooleanField(default=False)

    def send(self):
        res = send_otp(self.mobile_number, self.code)
        if res:
            self.send_count += 1
            self.save()
        return res


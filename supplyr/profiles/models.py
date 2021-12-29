from datetime import time
from django.db import models
from django_mysql.models import EnumField
import random
import string
from os.path import splitext
from django.utils import timezone
from supplyr.profiles.data import STATE_CHOICES,CURRENCY_CHOICES

def get_document_upload_path(instance, filename, document_category):
    file, ext = splitext(filename)
    new_filename = document_category + ext
    return f"documents/{ instance.id }/{ new_filename }"

def get_gst_upload_path(instance, filename):
    return get_document_upload_path(instance, filename, 'gst')


class SellerProfile(models.Model):
    class EntityTypes(models.TextChoices):
        PVTLTD = 'pvtltd', 'Private Limited'
        LLP = 'llp', 'Limited Liablity Partnership'
        PARTNER = 'part', 'Partnership'
        PROPRIETERSHIP = 'prop', 'Propertieship'

    class EntityCategory(models.TextChoices):
        MANUFACTURER = 'M', 'Manufacturer'
        DISTRIBUTOR = 'D', 'Distributer'
        WHOLESELLER = 'W', 'Wholeseller'
        
    class SellerStatusChoice(models.TextChoices):
        PENDING_APPROVAL = 'pending_approval', 'Pending Approval'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        NEED_MORE_INFO = 'need_more_info', 'Need More Information'
        PERMANENTLY_REJECTED = 'permanently_rejected', 'Permanently Rejected'
        CATEGORIES_SELECTED = "categories_selected","Categories Selected"
        NEW = 'new',"New"

    owner = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='seller_profiles')
    business_name = models.CharField(max_length=100, blank=True, null=True)
    entity_category = EnumField(choices=EntityCategory.choices, blank=True, null=True) 
    entity_type = EnumField(choices=EntityTypes.choices, blank=True, null=True)
    is_gst_enrolled = models.BooleanField(default=False, blank=True, null=True)
    gst_number = models.CharField(max_length=20, blank=True, null=True)
    pan_number = models.CharField(max_length=15, blank=True, null=True)
    tan_number = models.CharField(max_length=15, blank=True, null=True)
    
    default_currency = EnumField(default="INR",choices=CURRENCY_CHOICES)
    currency_representation = models.CharField(default="₹",max_length=75,null=True,blank=True)
    
    gst_certificate = models.FileField(upload_to=get_gst_upload_path, max_length=150, blank=True, null=True)
    operational_fields = models.ManyToManyField('inventory.Category', blank=True)
    invoice_prefix = models.CharField(max_length=12,null=True,blank=True)
    status = EnumField(default="new",choices=SellerStatusChoice.choices, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    connection_code = models.CharField(max_length=15)
    created_at = models.DateTimeField(default=timezone.now)
    
    # @property
    # def is_approved(self):
    #     if self.status == "approved":
    #         return True
    #     elif self.status == "rejected":
    #         return False
    #     elif self.status == "need_more_info":
    #         return "need_more_info"
    #     else:
    #         return "permanently_rejected"

    def generate_connection_code(self):
        if self.connection_code:
            return self.connection_code
            
        alpha = ''.join(random.choice(string.ascii_uppercase) for i in range(2))
        numeric =  ''.join(random.choice(string.digits) for i in range(8))
        code = alpha + numeric
        self.connection_code = code
        self.save()
        return code

    def __str__(self):
        return self.business_name or '--seller--'


    class Meta:
        verbose_name_plural = 'Seller Profiles'
        
    @property
    def gst_certificate_url(self):
        try:
            url = self.gst_certificate.url
        except:
            url = ''
        return url


class BuyerProfile(models.Model):

    owner = models.ForeignKey('core.User', on_delete=models.CASCADE, related_name='buyer_profiles', null=True, blank=True)
    business_name = models.CharField(max_length=100, blank=True, null=True)
    favourite_products = models.ManyToManyField('inventory.Product', related_name='marked_favourite_by', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.business_name} ({self.id})'

    class Meta:
        """Meta definition for BuyerProfile."""

        verbose_name = 'BuyerProfile'
        verbose_name_plural = 'BuyerProfiles'


class ManuallyCreatedBuyer(models.Model):
    """
    This model is used to store information of a buyer who is created by a salesperson, and his user is not created yet.
    We will enter his credentials in this table, and if the user joins in future, we will ask the user to claim the corresponding profile.
    """
    buyer_profile = models.ForeignKey('profiles.BuyerProfile', on_delete = models.CASCADE)
    email = models.CharField(max_length=100)
    mobile_number = models.CharField(max_length=14)
    created_by = models.ForeignKey('profiles.SalespersonProfile', on_delete=models.RESTRICT, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_settled = models.BooleanField(default=False)


class BuyerAddress(models.Model):
    STATE_CHOICES = STATE_CHOICES
    
    name = models.CharField(max_length=100)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200)
    pin = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    state = EnumField(choices=STATE_CHOICES)
    phone = models.CharField(max_length=15)

    is_default = models.BooleanField(default=False)

    owner = models.ForeignKey('profiles.BuyerProfile', on_delete=models.CASCADE,related_name="buyer_address")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner'], condition=models.Q(is_default=True), name='unique_default_address'), # Not supported in MySQL
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            BuyerAddress.objects.filter(is_active=True, owner_id=self.owner_id).exclude(pk=self.pk).update(is_default=False)
            
    def __str__(self):
        return f'{self.owner}'

class BuyerSellerConnection(models.Model):
    """Model definition for BuyerSellerConnection."""

    buyer = models.ForeignKey('profiles.BuyerProfile', on_delete=models.RESTRICT, related_name='connections')
    seller = models.ForeignKey('profiles.SellerProfile', on_delete=models.RESTRICT, related_name='connections')
    generic_discount = models.DecimalField(decimal_places=2,max_digits=6,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta definition for BuyerSellerConnection."""

        verbose_name = 'BuyerSellerConnection'
        verbose_name_plural = 'BuyerSellerConnections'
        unique_together = ('seller', 'buyer', 'is_active', 'deactivated_at')


class SalespersonProfile(models.Model):
    owner = models.ForeignKey('core.User', on_delete=models.RESTRICT, related_name='salesperson_profiles', blank=True, null=True)
    seller = models.ForeignKey('profiles.SellerProfile', on_delete=models.RESTRICT, related_name='salespersons')
    is_active = models.BooleanField(default=True)

class SalespersonPreregisteredUser(models.Model):
    """
    When a seller adds a salesperson email, it will be added here. WHen the salesperson signs up, he will be linked to the profile
    """
    salesperson_profile = models.ForeignKey(SalespersonProfile, on_delete=models.CASCADE, related_name='preregistrations')
    email = models.CharField(max_length=150)
    is_settled = models.BooleanField(default=False)
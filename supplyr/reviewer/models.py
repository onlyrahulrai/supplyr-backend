from random import choices
from django.db import models
from supplyr.core.models import User

from django.utils import timezone
from supplyr.profiles.models import SellerProfile
from django_mysql.models import EnumField
# Create your models here.

class SellerProfileReview(models.Model):
    '''
        SellerProfileReview aims is to create History on user profile update state by the reviewer.
    '''
    
    reviewer = models.ForeignKey(User,on_delete=models.CASCADE,null=True,blank=True)
    seller = models.ForeignKey(SellerProfile,on_delete=models.CASCADE,null=True,blank=True,related_name="seller_profile_review")
    is_approved = models.BooleanField(default=False)
    status = EnumField(default="new",choices=SellerProfile.SellerStatusChoice,blank=True,null=True)
    comments = models.TextField(null=True,blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    @property
    def seller_profile_review_approved_status(self):
        if self.is_approved:
            return "approved"
        else:
            return "unapproved"
        
    @property
    def seller_profile_review_rejected_status(self):
        if self.is_approved:
            return "rejected"
        else:
            return "deny"
        
    def __str__(self):
        return f'{self.seller.business_name} {self.seller_profile_review_approved_status}'
from django.db import models
from django_mysql.models import EnumField

# Create your models here.

class BuyerAddress(models.Model):
    STATE_CHOICES = (('KA', 'Karnataka'), ('AP', 'Andhra Pradesh'), ('KL', 'Kerala'), ('TN', 'Tamil Nadu'), ('MH', 'Maharashtra'), ('UP', 'Uttar Pradesh'), ('GA', 'Goa'), ('GJ', 'Gujarat'), ('RJ', 'Rajasthan'), ('HP', 'Himachal Pradesh'), ('JK', 'Jammu and Kashmir'), ('TG', 'Telangana'), ('AR', 'Arunachal Pradesh'), ('AS', 'Assam'), ('BR', 'Bihar'), ('CG', 'Chattisgarh'), ('HR', 'Haryana'), ('JH', 'Jharkhand'), ('MP', 'Madhya Pradesh'), ('MN', 'Manipur'), ('ML', 'Meghalaya'), ('MZ', 'Mizoram'), ('NL', 'Nagaland'), ('OR', 'Orissa'), ('PB', 'Punjab'), ('SK', 'Sikkim'), ('TR', 'Tripura'), ('UA', 'Uttarakhand'), ('WB', 'West Bengal'), ('AN', 'Andaman and Nicobar'), ('CH', 'Chandigarh'), ('DN', 'Dadra and Nagar Haveli'), ('DD', 'Daman and Diu'), ('DL', 'Delhi'), ('LD', 'Lakshadweep'), ('PY', 'Pondicherry'))
    
    name = models.CharField(max_length=100)
    line1 = models.CharField(max_length=200)
    line2 = models.CharField(max_length=200)
    pin = models.CharField(max_length=10)
    city = models.CharField(max_length=50)
    state = EnumField(choices=STATE_CHOICES)
    phone = models.CharField(max_length=15)

    is_default = models.BooleanField(default=False)

    owner = models.ForeignKey('core.BuyerProfile', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['owner'], condition=models.Q(is_default=True), name='unique_default_address'), # Not supported in MySQL
        ]
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_default:
            BuyerAddress.objects.filter(is_active=True, owner_id=self.owner_id).exclude(pk=self.pk).update(is_default=False)

class BuyerSellerConnection(models.Model):
    """Model definition for BuyerSellerConnection."""

    buyer = models.ForeignKey('core.BuyerProfile', on_delete=models.RESTRICT, related_name='connections')
    seller = models.ForeignKey('core.SellerProfile', on_delete=models.RESTRICT, related_name='connections')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    deactivated_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        """Meta definition for BuyerSellerConnection."""

        verbose_name = 'BuyerSellerConnection'
        verbose_name_plural = 'BuyerSellerConnections'
        unique_together = ('seller', 'buyer', 'is_active', 'deactivated_at')

from django.db import models
from django.contrib.auth import get_user_model

from django_mysql.models import Model

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
    

class Variant(Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')

    option1_name = models.CharField(max_length=30, blank=True, null=True)
    option1_value = models.CharField(max_length=50, blank=True, null=True)

    option2_name = models.CharField(max_length=30, blank=True, null=True)
    option2_value = models.CharField(max_length=30, blank=True, null=True)

    option3_name = models.CharField(max_length=50, blank=True, null=True)
    option3_value = models.CharField(max_length=50, blank=True, null=True)

    quantity = models.PositiveIntegerField(default=0)
    price = models.DecimalField(default=0, decimal_places=2, max_digits=12)
    sale_price = models.DecimalField(default=0, decimal_places=2, max_digits=12)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


# class VariantImage(Model):
#     variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
#     image = models.ImageField()
#     serial = models.PositiveSmallIntegerField()
#     uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)





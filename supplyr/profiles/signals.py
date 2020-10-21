from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import BuyerAddress

@receiver(post_save, sender=BuyerAddress)
def enforce_single_default_address(sender, instance, created, **kwargs):
    print("Came in signal ", instance, created)
    if created:
        pass
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.files.base import ContentFile
from .models import ProductImage
from PIL import Image
from io import BytesIO

@receiver(post_save, sender=ProductImage)
def generate_thumbnail(sender, instance, created, **kwargs):
    print("Came in signal ", instance, created)
    # if isntance.is_default == True:

    if created:
        # instance.generate_sizes()
        pass
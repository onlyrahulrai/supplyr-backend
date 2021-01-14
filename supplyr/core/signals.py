from django.contrib.auth import get_user_model
from supplyr.core.functions import check_and_link_manually_created_profiles
from allauth.account.signals import email_confirmed
from django.dispatch import receiver

User = get_user_model()

@receiver(email_confirmed)
def on_email_confirm(request, email_address, **kwargs):
    if user := User.objects.filter(email=email_address).first():
        if user.is_credentials_verified:
            check_and_link_manually_created_profiles(user)
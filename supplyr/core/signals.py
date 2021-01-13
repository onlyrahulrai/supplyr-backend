from django.contrib.auth import get_user_model
from supplyr.core.functions import check_and_link_manually_created_buyer
from allauth.account.signals import email_confirmed
from django.dispatch import receiver

User = get_user_model()

@receiver(email_confirmed)
def on_email_confirm(request, email_address, **kwargs):
    print("CAME TO SIGNASL ", email_address)
    if user := User.objects.filter(email=email_address).first():
        check_and_link_manually_created_buyer(user)
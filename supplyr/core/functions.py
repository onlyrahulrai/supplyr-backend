from django.db.models import Q
from supplyr.profiles.models import ManuallyCreatedBuyer

def check_and_link_manually_created_buyer(user):
    if manual_buyer := ManuallyCreatedBuyer.objects.filter(Q(mobile_number=user.mobile_number) | Q(email=user.email)).first():
        manual_buyer.buyer_profile.owner = user
        manual_buyer.buyer_profile.save()
        manual_buyer.is_settled = True
        manual_buyer.save()
        
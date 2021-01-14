from django.db.models import Q
from supplyr.profiles.models import ManuallyCreatedBuyer, SalespersonPreregisteredUser

def check_and_link_manually_created_profiles(user):
    if manual_buyer := ManuallyCreatedBuyer.objects.filter(Q(mobile_number=user.mobile_number) | Q(email=user.email)).first():
        manual_buyer.buyer_profile.owner = user
        manual_buyer.buyer_profile.save()
        manual_buyer.is_settled = True
        manual_buyer.save()

    if preregistered_user := SalespersonPreregisteredUser.objects.filter(email = user.email).first():
        preregistered_user.salesperson_profile.owner = user
        preregistered_user.salesperson_profile.save()
        preregistered_user.is_settled = True
        preregistered_user.save()

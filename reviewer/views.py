from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, admin_only
from supplyr.core.models import User
from supplyr.inventory.models import Category
from .utils import paginate_func
from supplyr.profiles.models import SellerProfile
from django.views.decorators.csrf import csrf_exempt
import json
from .models import SellerProfileReview
from django.shortcuts import get_object_or_404
from supplyr.core.models import User
from supplyr.profiles.models import SellerProfile
from .filters import SellerProfileFilter
from supplyr.profiles.models import SellerProfile
from .forms import LoginForm
import json



@login_required(login_url="login")
@admin_only
def dashboard(request):
    unverified_seller = User.objects.filter(
        seller_profiles__status="rejected").order_by("-date_joined")
    verified_seller = User.objects.filter(
        seller_profiles__status="approved").order_by("-date_joined")
    category_count = Category.objects.all().count()
    verified = request.GET.get('verified', 1)
    unverified = request.GET.get('unverified', 1)
    verified_sellers = paginate_func(request, verified_seller, verified)
    unverified_sellers = paginate_func(request, unverified_seller, unverified)
    
    seller_profiles = SellerProfile.objects.all()
    user_filter = SellerProfileFilter(request.GET,queryset=seller_profiles)
    filter = request.GET.get('filter', 1)
    profiles = paginate_func(request, user_filter.qs, filter,count=7)
    
    
    context = {
        "unverified_sellers": unverified_sellers,
        "verified_sellers": verified_sellers,
        "total_verified_seller": verified_seller.count(),
        "total_unverified_seller": unverified_seller.count(),
        "category_count": category_count,
        "profiles":profiles,
        "filter":user_filter
    }
    return render(request, "index.html", context)


def seller_profiles(request):
    objects = SellerProfile.objects.all()
    user_filter = SellerProfileFilter(request.GET,queryset=objects)
    profiles = user_filter.qs
    print(profiles)
    seller_profiles = [{"id":seller_profile.id,"owner":seller_profile.owner.name,"business_name":seller_profile.business_name,"entity_category":seller_profile.entity_category,"entity_type":seller_profile.entity_type,"is_gst_enrolled":seller_profile.is_gst_enrolled,"is_active":seller_profile.is_active,"status":seller_profile.status} for seller_profile in profiles]
    return JsonResponse(seller_profiles,safe=False)


@login_required(login_url="login")
@admin_only
def customer(request, pk):
    seller_profile = get_object_or_404(SellerProfile, pk=pk)
    seller_profile_review = SellerProfileReview.objects.filter(
        seller=seller_profile).order_by("-id")
    history = request.GET.get("history", 1)
    reviews = paginate_func(request, seller_profile_review, history, count=3)
    context = {
        "seller_profile": seller_profile,
        "reviews": reviews,
    }
    return render(request, "profile.html", context)


@csrf_exempt
def approve_seller(request):
    data = json.loads(request.body)
    sellerProfileId = data.get("sellerProfileId")
    action = data.get("action")
    comments = data.get("comment")
    user_id = data.get("userId")
    print(action)
    seller_profile = SellerProfile.objects.get(id=sellerProfileId)
    user = get_object_or_404(User, id=user_id)
    if action == SellerProfile.SellerStatusChoice.APPROVED:
        seller_profile.status="Approved"
    elif action == SellerProfile.SellerStatusChoice.REJECTED:
        seller_profile.status="Rejected"
    elif action == SellerProfile.SellerStatusChoice.NEED_MORE_INFO:
        seller_profile.status="need_more_info"
    elif action == SellerProfile.SellerStatusChoice.PERMANENTLY_REJECTED:
        seller_profile.status="permanently_rejected"
    
    print(action)
    seller_profile_review = SellerProfileReview.objects.create(
            reviewer=user, seller=seller_profile, status=action, comments=comments)
    seller_profile.save()
    seller_profile_review.save()
    
    return JsonResponse({"data": data, "success": "true"})

@unauthenticated_user
def mylogin(request):
    form = LoginForm(request.POST or None)
    msg = None
    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data.get("email")
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                return redirect("dashboard")
            else:    
                msg = 'Invalid credentials' 
        else:
            msg = 'Error validating the form' 
    context = {
        "form":form,
        "msg":msg
    }
    return render(request, "accounts/login.html",context)


def mylogout(request):
    logout(request)
    return redirect("login")

    
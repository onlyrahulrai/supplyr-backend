from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, logout, login
from django.contrib.auth.decorators import login_required
from .decorators import unauthenticated_user, admin_only
from supplyr.core.models import User
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
import json
from .forms import LoginForm
from supplyr.profiles.serializers import SellerProfilingSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from .utils import CustomPageNumber




@login_required(login_url="login")
@admin_only
def dashboard(request):
    return render(request, "index.html")


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

@api_view(["GET"])
@permission_classes((permissions.AllowAny,))
def seller_profiles(request):
    if request.method == "GET":
        paginator = CustomPageNumber()
        paginator.page_size = 3
        objects = SellerProfile.objects.all().order_by("id")
        filters = SellerProfileFilter(request.GET,queryset=objects)
        result_page = paginator.paginate_queryset(filters.qs, request)
        serializer = SellerProfilingSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)
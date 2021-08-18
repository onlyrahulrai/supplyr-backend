from rest_framework.response import Response
from supplyr.inventory.models import Category
from supplyr.inventory.serializers import CategoriesSerializer2
from django.http import JsonResponse
from django.http.response import HttpResponse
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
from .forms import CategoryCreateForm, LoginForm
from supplyr.profiles.serializers import SellerProfilingSerializer
from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from .utils import CustomPageNumber
from rest_framework.decorators import api_view


@login_required(login_url="login")
@admin_only
def dashboard(request):
    # It is a dashboard route. which is responsible for the reviewer dashboard main page.
    return render(request, "index.html")


@login_required(login_url="login")
@admin_only
def customer(request, pk):
    # It is a seller profile Detail Route. which is responsible for display the seller profile detail.
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
    # This route is responsible for handling the seller account status. where the reviewer can approve, reject, permanently reject, request some necessary information from the seller, etc.
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
    # This is a Login route.which is responsible for authenticating an user on the server.
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
    # This is the Logout route. which is responsible for removing all the access of users from the server after authentication on the server.
    logout(request)
    return redirect("login")

@api_view(["GET"])
@permission_classes((permissions.AllowAny,))
def seller_profiles(request):
    # This is an API for returning the seller profile. where implemented so many things like pagination, filter, etc.
    if request.method == "GET":
        paginator = CustomPageNumber()
        paginator.page_size = 3
        objects = SellerProfile.objects.all().order_by("id")
        filters = SellerProfileFilter(request.GET,queryset=objects)
        result_page = paginator.paginate_queryset(filters.qs, request)
        serializer = SellerProfilingSerializer(result_page,many=True)
        return paginator.get_paginated_response(serializer.data)
    
@login_required(login_url="login")
@admin_only
def categories_list(request):
    categories = Category.objects.filter(is_active=True,parent=None,seller=None)
    serializer = CategoriesSerializer2(categories,many=True)
    context = {
        "categories":serializer.data
    }
    return render(request,"categories.html",context)

@login_required(login_url="login")
@admin_only
def category_action(request,pk=None):
    context = {
        "title":"Create action"
    }
    return render(request,"category_form.html",context)

@login_required(login_url="login")
@admin_only
def category_detail(request,pk=None):
    if request.method == "GET":
        category = get_object_or_404(Category,pk=pk)
        serializer = CategoriesSerializer2(category)
        return JsonResponse(serializer.data)
    
@csrf_exempt
@login_required(login_url="login")
@admin_only
def category_create(request,pk=None):
    if request.method == "POST":
        sub_categories = json.loads(request.POST.get("sub_categories"))
        form = CategoryCreateForm(request.POST,request.FILES)
        if form.is_valid():
            parent = form.save()
            for sub_category in sub_categories:
                create_sub_category = Category.objects.create(parent=parent,**sub_category)
                create_sub_category.save()
    return JsonResponse({"success":True,"status":200})

@csrf_exempt
@login_required(login_url="login")
@admin_only
def category_update(request,pk=None):
    if request.method == "POST":
        category = get_object_or_404(Category,pk=pk)
        sub_categories = json.loads(request.POST.get("sub_categories"))
        form = CategoryCreateForm(request.POST,request.FILES,instance=category)
        if form.is_valid():
            parent = form.save()
            sub_categories_initial = list(parent.sub_categories.values_list('id', flat=True))
            sub_categories_final = []
            for sub_category in sub_categories:
                updated_sub_category = Category(parent=parent,**sub_category)
                updated_sub_category.save()
                sub_categories_final.append(updated_sub_category.id)
                
            sub_categories_to_remove = [sc for sc in sub_categories_initial if sc not in sub_categories_final]
            Category.objects.filter(id__in=sub_categories_to_remove).update(is_active = False)
            return JsonResponse({"success":True,"status":200})
        else:
            return JsonResponse({"success":False,"status":304})

@csrf_exempt
@login_required(login_url="login")
@admin_only
def category_delete(request,pk=None):
    if request.method == "DELETE":
        category = get_object_or_404(Category,pk=pk)
        category.is_active = False
        category.save()
        return JsonResponse({"success":True,"status":200})
    
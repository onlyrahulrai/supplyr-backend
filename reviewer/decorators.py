from django.http import HttpResponse
from django.shortcuts import redirect



# This is a decorator function used for checking user in authenticated or not
def unauthenticated_user(view_func):
    def wrapper_function(request,*args,**kwargs):
        if request.user.is_authenticated:
            return redirect("dashboard")
        else:
            return view_func(request,*args,**kwargs)
    return wrapper_function

# This is a decorator function used for checking user role.and decide which user able to redirect to the dashboard route 
def admin_only(view_func):
    def wrapper_function(request,*args,**kwargs):
        group = None
        if request.user.groups.exists():
            group = request.user.groups.all()[0].name
            
        if group == "admin":
            return view_func(request,*args,**kwargs)
        else:
            return HttpResponse("You are not authorized to view this page")
        
    return wrapper_function
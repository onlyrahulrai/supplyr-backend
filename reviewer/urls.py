from django.urls import path
from . import views
from django.contrib.auth import views as auth_views



urlpatterns = [ 
    path("",views.dashboard,name="dashboard"),               
    path("seller_profiles/",views.seller_profiles,name="seller_profiles"),               
    path("customer/<str:pk>/",views.customer,name="customer"),               
    path("approve-seller/",views.approve_seller,name="approve-seller"),                             
    path("login/",views.mylogin,name="login"),               
    path("logout/",views.mylogout,name="logout"),   
    path("reset_password/",auth_views.PasswordResetView.as_view(template_name="accounts/password_reset.html",html_email_template_name='registration/password_reset_email.html',extra_email_context={'password_reset_url_base':'127.0.0.1:8000/v1/reviewer/reset/'}),name="reset_password"),            
    path("reset_password_sent/",auth_views.PasswordResetDoneView.as_view(template_name="accounts/password_reset_sent.html"),name="password_reset_done"),            
    path("reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(template_name="accounts/password_reset_form.html"),name="password_reset_confirm"),            
    path("reset_password_complete/",auth_views.PasswordResetCompleteView.as_view(template_name="accounts/password_reset_done.html"),name="password_reset_complete"),            
]
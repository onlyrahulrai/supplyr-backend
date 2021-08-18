from django.forms import fields
from supplyr.inventory.models import Category
from django import forms
from .models import SellerProfileReview




# This is a login form.use for authenticating an user by their email and password. 
class LoginForm(forms.Form):
    email= forms.CharField(
        widget=forms.TextInput(
            attrs={
                "placeholder" : "Email",                
                "class": "form-control"
            }
        ))
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "placeholder" : "Password",                
                "class": "form-control"
            }
        ))
    
class CategoryCreateForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name","image"]
        

        
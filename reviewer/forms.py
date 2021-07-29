from django import forms
from .models import SellerProfileReview
from django import forms



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
        

        
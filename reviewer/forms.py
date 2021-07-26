from django import forms
from .models import SellerProfileReview
from django import forms




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
        
class SellerProfileReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SellerProfileReviewForm, self).__init__(*args, **kwargs)
        self.fields['reviewer'].disabled = True
        self.fields['seller'].disabled = True
            
    class Meta:
        model = SellerProfileReview
        fields = "__all__"
        
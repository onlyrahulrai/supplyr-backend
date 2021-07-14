from django import forms
from supplyr.profiles.models import SellerProfile
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


class SellerProfileForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(SellerProfileForm, self).__init__(*args, **kwargs)
        self.fields['owner'].disabled = True
        self.fields["business_name"].disabled = True
        self.fields["entity_category"].disabled = True
        self.fields["entity_type"].disabled = True
        self.fields["is_gst_enrolled"].disabled = True
        self.fields["gst_number"].disabled = True
        self.fields["pan_number"].disabled = True
        self.fields["tan_number"].disabled = True
        self.fields["gst_certificate"].disabled = True
        self.fields["operational_fields"].disabled = True
        self.fields["is_active"].disabled = True
        self.fields["connection_code"].disabled = True
        self.fields["created_at"].disabled = True
        

    class Meta:
        model = SellerProfile
        fields = "__all__"
        
class SellerProfileReviewForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SellerProfileReviewForm, self).__init__(*args, **kwargs)
        self.fields['reviewer'].disabled = True
        self.fields['seller'].disabled = True
            
    class Meta:
        model = SellerProfileReview
        fields = "__all__"

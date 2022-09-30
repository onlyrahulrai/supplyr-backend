from django.contrib import admin
from .models import BuyerAddress, BuyerSellerConnection, BuyerProfile, SalespersonPreregisteredUser, SellerProfile, SalespersonProfile, ManuallyCreatedBuyer, AddressState
from django import forms
from prettyjson import PrettyJSONWidget
import json

class SellerProfileForm(forms.ModelForm):    
    class Meta:
        model = SellerProfile
        fields = '__all__'
        widgets = {
            'user_settings': PrettyJSONWidget(attrs={'initial': 'parsed'})
        }
        
    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields["user_settings"].widget.attrs.update({'required':False,"value":{}})
        

    def clean_user_settings(self,*args,**kwargs):
        user_settings = self.instance.default_user_settings if self.cleaned_data.get("user_settings",{}) == None else self.cleaned_data.get("user_settings",{})
            
        if ("translations" not in user_settings):
            user_settings['translations'] = self.instance.default_user_settings.get("translations")
        
        if ("invoice_options" not in user_settings):
            user_settings["invoice_options"] = self.instance.default_user_settings.get("invoice_options")
            
        translations = user_settings.get("translations",{})
        
        if "quantity" not in translations:
            translations.update({"quantity":"Quantity"})
            
        user_settings.get("translations").update(translations)
        
        invoice_options = user_settings.get("invoice_options")
            
        if "generate_at_status" not in invoice_options:
            invoice_options.update({"generate_at_status":self.instance.default_user_settings.get("invoice_options",{}).get("generate_at_status")})
            
        if "template" not in invoice_options:
            invoice_options.update({"template":self.instance.invoice_template})
                
        user_settings.get("invoice_options").update(invoice_options)
            
        return user_settings

@admin.register(BuyerAddress)
class BuyerAddressAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name',
        'line1',
        'line2',
        'pin',
        'city',
        'state',
        'is_default',
        'owner',
        'is_active',
    )
    list_filter = ('is_default', 'owner', 'is_active')
    search_fields = ('name',)
    list_editable = ('is_default', 'is_active')

@admin.register(BuyerSellerConnection)
class BuyerSellerConnectionAdmin(admin.ModelAdmin):
    list_display = ("id","buyer","seller")

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    form = SellerProfileForm

admin.site.register(BuyerProfile)
admin.site.register(SalespersonProfile)
admin.site.register(ManuallyCreatedBuyer)
admin.site.register(SalespersonPreregisteredUser)
admin.site.register(AddressState)
from django.contrib import admin
from .models import BuyerAddress, BuyerSellerConnection, BuyerProfile, SalespersonPreregisteredUser, SellerProfile, SalespersonProfile, ManuallyCreatedBuyer, AddressState
from django import forms
from prettyjson import PrettyJSONWidget

class SellerProfileForm(forms.ModelForm):
  class Meta:
    model = SellerProfile
    fields = '__all__'
    widgets = {
      'myjsonfield': PrettyJSONWidget(),
    }

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
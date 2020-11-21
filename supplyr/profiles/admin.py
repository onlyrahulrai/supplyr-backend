from django.contrib import admin

from .models import BuyerAddress, BuyerSellerConnection, BuyerProfile, SellerProfile, SalespersonProfile


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

admin.site.register(SellerProfile)
admin.site.register(BuyerProfile)
admin.site.register(BuyerSellerConnection)
admin.site.register(SalespersonProfile)
from django.contrib import admin
from .models import *

@admin.register(Category)
class PetAdmin(admin.ModelAdmin):
    list_filter = ('is_active', )
admin.site.register(Product)
admin.site.register(Variant)
admin.site.register(ProductImage)
admin.site.register(Tags)
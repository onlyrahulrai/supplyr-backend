from django.contrib import admin
from .models import *

@admin.register(Category)
class PetAdmin(admin.ModelAdmin):
    list_filter = ('is_active', )
    
@admin.register(Product)
class CategoryAdmin(admin.ModelAdmin):
    list_filter = ("owner",)    

admin.site.register(Variant)
admin.site.register(ProductImage)
admin.site.register(Tags)
admin.site.register(Vendors)

@admin.register(AutoCategoryRule)
class AutoCategoryRuleAdmin(admin.ModelAdmin):
    list_filter = ("category",) 

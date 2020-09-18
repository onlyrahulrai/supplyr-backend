from django.contrib import admin

from .models import User, SellerProfile, Category, SubCategory

admin.site.register(User)
admin.site.register(SellerProfile)
admin.site.register(Category)
admin.site.register(SubCategory)

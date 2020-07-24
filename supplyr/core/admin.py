from django.contrib import admin

from .models import User, Profile, Category, SubCategory

admin.site.register(User)
admin.site.register(Profile)
admin.site.register(Category)
admin.site.register(SubCategory)

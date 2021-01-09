from django.contrib import admin

from .models import User, MobileVerificationOTP

admin.site.register(User)
admin.site.register(MobileVerificationOTP)
from django.contrib import admin

from .models import User, Entity

admin.site.register(User)
admin.site.register(Entity)
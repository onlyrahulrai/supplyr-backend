"""supplyr URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.generic import RedirectView
from rest_framework.schemas import get_schema_view
from rest_framework.documentation import include_docs_urls
# from rest_framework_simplejwt.views import TokenRefreshView
# from rest_framework.authtoken.views import obtain_auth_token


# router = routers.DefaultRouter()
# router.register(r'users', UserDetailsViewSet)

# Optional_Param = '(?:(?P<app_type>(buyer|seller))/)?'
# Mandatory_Param = '^(?P<app_type>(buyer|seller))/'

_urlpatterns = [
    path('', include('supplyr.core.urls')),
    path('inventory/', include('supplyr.inventory.urls')),
    path('profile/', include('supplyr.profiles.urls')),
    path('register/', include('dj_rest_auth.registration.urls')),
    path('orders/', include('supplyr.orders.urls')),
    path('discounts/', include('supplyr.discounts.urls')),
]


urlpatterns = [
    path("api/",include_docs_urls(title="Supplyr API",description="B2B service API"),name="Supplyr backend docs"),
    path("schema/",get_schema_view(
        title="Supplyr API",
        description="B2B service API",
        version="1.0.0"
    ),name="schema"),
    re_path('^v1/(?P<api_source>(buyer|seller|sales))/', include(_urlpatterns)),
    re_path('^reviewer/', include("supplyr.reviewer.urls")),
    path('', RedirectView.as_view(pattern_name='dashboard', permanent=False)),
    path('admin/', admin.site.urls),
    path('register/', include('dj_rest_auth.registration.urls')),

    # The below url is required for password reset mail to be sent, otherwise it raises exception (UPDATE: It started working without this after custom email template)
    # re_path(r'^password-reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,50})/$',
    #     TemplateView.as_view(template_name="password_reset_confirm.html"),
    #     name='password_reset_confirm'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
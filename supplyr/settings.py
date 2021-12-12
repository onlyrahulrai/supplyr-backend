"""
Django settings for supplyr project.

Generated by 'django-admin startproject' using Django 3.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from datetime import timedelta

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'bomxq7-xhspd_u1%y4(hcwfszd(-eaw1o^m3#j&$g!drk@e%an'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['.supplyr.tk']


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',

    'django_extensions',
    'django_mysql',

    'supplyr.core.apps.CoreConfig',
    'supplyr.inventory.apps.InventoryConfig',
    'supplyr.profiles.apps.ProfilesConfig',
    'supplyr.orders.apps.OrdersConfig',
    'supplyr.reviewer.apps.ReviewerConfig',
    
    
    

    'allauth',
    'allauth.account',
    'dj_rest_auth',
    'dj_rest_auth.registration',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'supplyr.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],           
        },
    },
]

WSGI_APPLICATION = 'supplyr.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'amojo',
        'PASSWORD': 'z238@hp',
        'OPTIONS': {
            # Tell MySQLdb to connect with 'utf8mb4' character set
            'charset': 'utf8mb4',
        },
    }
}

SITE_ID = 1

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    # {
    #     'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    # },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 6,
        }
    },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    # },
    # {
    #     'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    # },
]

AUTH_USER_MODEL = 'core.User'


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'
# TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATICFILES_DIRS = [
    os.path.join(BASE_DIR,"static")
]

STATIC_URL = '/static/'

MEDIA_ROOT = 'media/'
MEDIA_URL = 'media/'

REST_FRAMEWORK = {
    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ],
    "DEFAULT_SCHEMA_CLASS": "rest_framework.schemas.coreapi.AutoSchema",
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # 'rest_framework.authentication.TokenAuthentication',
        'dj_rest_auth.jwt_auth.JWTCookieAuthentication',
    ],
    'DEFAULT_PAGINATION_CLASS': 'supplyr.core.pagination.CustomPagination',
    'PAGE_SIZE': 30,
}

# dj-rest-auth configuration start

REST_USE_JWT = True
# JWT_AUTH_COOKIE = 'sauth'
# JWT_AUTH_HTTPONLY = True
# JWT_AUTH_SAMESITE = False
OLD_PASSWORD_FIELD_ENABLED = True

REST_AUTH_SERIALIZERS = {
    'USER_DETAILS_SERIALIZER': 'supplyr.profiles.serializers.UserDetailsSerializer',
    'JWT_SERIALIZER': 'supplyr.core.serializers.CustomJWTSerializer',
    'LOGIN_SERIALIZER': 'supplyr.core.serializers.CustomLoginSerializer',
    'PASSWORD_RESET_SERIALIZER': 'supplyr.core.serializers.CustomPasswordResetSerializer',
    "PASSWORD_RESET_CONFIRM_SERIALIZER":"supplyr.core.serializers.PasswordResetConfirmSerializer"
}
REST_AUTH_REGISTER_SERIALIZERS = {
    'REGISTER_SERIALIZER': 'supplyr.core.serializers.CustomRegisterSerializer'
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=7),
}

#Change ACCOUNT_EMAIL_VERIFICATION to 'optional' to setup verification mails. (After configuring SMTP)
ACCOUNT_EMAIL_VERIFICATION = "optional"
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_ADAPTER='supplyr.core.auth.CustomAccountAdapter'
ACCOUNT_USER_DISPLAY= lambda user: user.name

MOBILE_VERIFICATION_OTP_EXPIRY_MINUTES = 10


URL_FRONTEND = 'https://supplier.amojo.com/'

AUTHENTICATION_BACKENDS = [
    # Needed to login by username in Django admin, regardless of `allauth`
    # 'django.contrib.auth.backends.ModelBackend',

    # `allauth` specific authentication methods, such as login by e-mail
    'allauth.account.auth_backends.AuthenticationBackend',
]



# dj-rest-auth configuration end

CRISPY_TEMPLATE_PACK = "bootstrap4"

CORS_ORIGIN_WHITELIST = [
    #Insert production API url here
]


# Enable this to allow cross domain cookies
# CORS_ALLOW_CREDENTIALS = True 
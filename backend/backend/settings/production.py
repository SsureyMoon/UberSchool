from .base import *
import os
import dj_database_url


# DATABASES['default'] = dj_database_url.config()

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = os.environ["SECRET_KEY"]

ALLOWED_HOSTS = ["*", ]
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

DATABASES = {
    'default': {
        # 'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'ENGINE' : 'django.contrib.gis.db.backends.postgis',
        'NAME': 'uber_school',
        'USER': 'ubuntu',
        'PASSWORD': 'ubuntu',
        'HOST': '',                      # Empty for localhost through domain sockets or '127.0.0.1' for localhost through TCP.
        'PORT': '',                      # Set to empty string for default.
    }
}

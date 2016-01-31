# settings/prod.py
from os import environ as env
from .base import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = ((env.get('ADMIN_NAME'), env.get('ADMIN_EMAIL')),)
ROBOT = env.get('ROBOT')

SERVER_EMAIL = env.get('SERVER_EMAIL')
EMAIL_HOST = env.get('EMAIL_HOST')
EMAIL_PORT = env.get('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env.get('SERVER_EMAIL')
EMAIL_HOST_PASSWORD = env.get('EMAIL_HOST_PASSWORD')
EMAIL_SUBJECT_PREFIX = ""

SITE_URL = 'http://www' + env.get('ALLOWED_HOSTS')
ALLOWED_HOSTS = (env.get('ALLOWED_HOSTS'),)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env.get('DB_NAME'),
        'USER': env.get('DB_USER'),
        'PASSWORD': env.get('DB_PASSWORD'),
        'HOST': env.get('DB_HOST'),
        'PORT': env.get('DB_PORT'),
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': env.get('CACHE_LOCATION'),
    }
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
        'logfile': {
            'level':'DEBUG',
            'class':'logging.FileHandler',
            'filename': '/var/www/forum/logs/django.log',
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console', 'logfile']
    },
}

from .base import *

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'naxosdb',
        'USER': 'tm',
        'PASSWORD': 'crimson',
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

INSTALLED_APPS += ('debug_toolbar',)

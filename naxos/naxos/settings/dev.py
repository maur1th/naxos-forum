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

# Enable template caching
# TEMPLATE_LOADERS = (
#     ('django.template.loaders.cached.Loader', (
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     )),
# )
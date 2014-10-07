# settings/local.py
from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# DATABASES = {}

# INSTALLED_APPS += ('debug_toolbar',)

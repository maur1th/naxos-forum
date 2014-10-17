# settings/local.py
from .base import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.postgresql_pycopg2',
#         'NAME': 'naxos'
        
#     }
# }

# INSTALLED_APPS += ('debug_toolbar.apps.DebugToolbarConfig',)

# settings/prod.py
from .base import *

DEBUG = {{debug_mode}}
TEMPLATE_DEBUG = DEBUG

ADMINS = (("{{admin_name}}", "{{admin_email}}"),)
ROBOT = "{{robot_name}}"

SERVER_EMAIL = "{{server_email}}"
EMAIL_HOST = "{{email_host}}"
EMAIL_PORT = "{{email_port}}"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "{{server_email}}"
EMAIL_HOST_PASSWORD = "{{email_host_password}}"
EMAIL_SUBJECT_PREFIX = ""

SITE_URL = "http://www.{{allowed_hosts}}"
ALLOWED_HOSTS = ("{{allowed_hosts}}",)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "{{db_name}}",
        "USER": "{{db_user}}",
        "PASSWORD": "{{db_password}}",
        "HOST": "{{db_host}}",
        "PORT": "{{db_port}}",
    }
}

CONN_MAX_AGE = None

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        "LOCATION": "{{cache_location}}",
    }
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
        },
        "logfile": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "/var/log/{{project_name}}/django.log",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console", "logfile"]
    },
}

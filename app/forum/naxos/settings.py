"""
Django settings for naxos project.

For more information on this file, see
https://docs.djangoproject.com/en/stable/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/stable/ref/settings/
"""

import os
from .utils.path import root, BASE_DIR
from .utils.keygen import SECRET_KEY  # Secret key from generator module


DEBUG = True if os.environ.get("DEBUG") == "1" else False

# static & media files settings
STATICFILES_DIRS = (root("static"),)
MEDIA_ROOT = root("media")

if os.environ["LOCAL_ENV"] == "1":
    STATIC_ROOT = root("static_root")
    STATIC_URL = "/static/"
    MEDIA_URL = "/media/"
else:
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
    AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
    AWS_S3_CUSTOM_DOMAIN = AWS_STORAGE_BUCKET_NAME + ".s3.amazonaws.com"

    STATICFILES_LOCATION = "static"
    STATICFILES_STORAGE = "naxos.utils.storages.StaticStorage"
    STATIC_URL = "https://{:s}/{:s}/".format(AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

    MEDIAFILES_LOCATION = "media"
    MEDIA_URL = "https://{:s}/{:s}/".format(AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
    DEFAULT_FILE_STORAGE = "naxos.utils.storages.MediaStorage"


# Security
RAW_HOSTS = (os.environ.get("HOSTNAME"), "forum", "localhost")
ALLOWED_HOSTS = tuple(filter(lambda x: x != None, RAW_HOSTS))
SECRET_KEY = SECRET_KEY


# Sessions
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_COOKIE_SECURE = False  # True for full HTTPS
CSRF_COOKIE_SECURE = False     # True for full HTTPS
SESSION_COOKIE_AGE = 15552000  # 6 months


# App conf
ADMINS = ((os.environ.get("ADMIN_NAME"), os.environ.get("ADMIN_EMAIL")),)
INSTALLED_APPS = (
    # Django Apps
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",

    # Third-party Apps
    "storages",
    "crispy_forms",

    # Project Apps
    "forum.apps.ForumConfig",
    "user.apps.UserConfig",
    "pm.apps.PMConfig",
    "blog.apps.BlogConfig",
    "utils.apps.UtilsConfig",
)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "naxos.urls"

WSGI_APPLICATION = "naxos.wsgi.application"

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_L10N = True
USE_TZ = True

AUTH_USER_MODEL = "user.ForumUser"

LOGIN_URL = "user:login"
LOGIN_REDIRECT_URL = "forum:top"

CRISPY_TEMPLATE_PACK = "bootstrap3"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            root("templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                "django.template.context_processors.debug",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "django.contrib.messages.context_processors.messages",
            ],
            "debug": DEBUG,
        },
    },
]


# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("DB_NAME", "postgres"),
        "USER": os.environ.get("DB_USER", "postgres"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "crimson"),
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", 5432),
    }
}
CONN_MAX_AGE = None


# Cache
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.memcached.PyLibMCCache",
        "LOCATION": os.environ.get("CACHE_LOCATION", "memcached"),
    }
}

# Logging
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "colored_verbose": {
            "()": "colorlog.ColoredFormatter",
            "format": "%(log_color)s%(levelname)-8s%(red)s%(module)-30s%(reset)s %(blue)s%(message)s"
        },
    },
    "handlers": {
        'colored_console': {
            'level': LOG_LEVEL,
            'class': 'logging.StreamHandler',
            'formatter': 'colored_verbose'
        }
    },
    'loggers': {
        '': {
            'level': LOG_LEVEL,
            'handlers': ['colored_console'],
        },
        'gunicorn.access': {
            'handlers': ['colored_console']
        },
        'gunicorn.error': {
            'handlers': ['colored_console']
        }
    }
}


# Email
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
SERVER_EMAIL = os.environ.get("SERVER_EMAIL")  # email address to use
EMAIL_HOST_USER = os.environ.get("SERVER_EMAIL")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_USE_TLS = True
EMAIL_SUBJECT_PREFIX = os.environ.get("EMAIL_SERVER_PREFIX", "")

# Debug
if DEBUG == True:
    INTERNAL_IPS = [os.environ.get("INTERNAL_IP")]
    INSTALLED_APPS += ("debug_toolbar",)
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.dummy.DummyCache",
        }
    }

"""
Django settings for naxos project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

from .util import root, BASE_DIR
from .secretKeyGen import SECRET_KEY  # Secret key from generator module


DEBUG = {{debug_mode}}

# Configuring directories
MEDIA_ROOT = root("media")
STATICFILES_DIRS = (root("static"),)

# Security
ALLOWED_HOSTS = ("{{allowed_hosts}}", "localhost")
SITE_URL = "http://www.{{allowed_hosts}}"
SECRET_KEY = SECRET_KEY
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = "DENY"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True

# App conf
ADMINS = (("{{admin_name}}", "{{admin_email}}"),)
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
    "crispy_forms",

    # Project Apps
    "forum",
    "user",
    "pm",
    "blog",
)

MIDDLEWARE_CLASSES = (
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.auth.middleware.SessionAuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.security.SecurityMiddleware",
)

ROOT_URLCONF = "naxos.urls"

WSGI_APPLICATION = "naxos.wsgi.application"

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Europe/Paris"
USE_I18N = True
USE_L10N = True
USE_TZ = False

STATIC_URL = "/static/"
MEDIA_URL = "/media/"

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

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "{{project_name}}",
        "USER": "{{app_user}}",
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

# Email
SERVER_EMAIL = "{{server_email}}"
EMAIL_HOST = "{{email_host}}"
EMAIL_PORT = "{{email_port}}"
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "{{server_email}}"
EMAIL_HOST_PASSWORD = "{{email_host_password}}"
EMAIL_SUBJECT_PREFIX = ""

# Misc
ROBOT = "{{robot_name}}"

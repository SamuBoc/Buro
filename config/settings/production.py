from .base import *
import os
import dj_database_url

DEBUG = False
SECRET_KEY = os.environ['SECRET_KEY']
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', '')
if _origins:
    CSRF_TRUSTED_ORIGINS = _origins.split(',')

DATABASES = {
    'default': dj_database_url.config(conn_max_age=600)
}

EMAIL_BACKEND  = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST     = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT     = 587
EMAIL_USE_TLS  = True
EMAIL_HOST_USER     = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

ENABLE_APP_SCHEDULERS = True

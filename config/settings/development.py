from .base import *
import dj_database_url

DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
ENABLE_APP_SCHEDULERS = False

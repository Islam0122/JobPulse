from .base import *

DEBUG = False
ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "HOST": env("PGHOST", default="db"),
        "USER": env("PGUSER", default="postgres"),
        "NAME": env("PGDATABASE", default="postgres"),
        "PASSWORD": env("PGPASSWORD", default="postgres"),
        "PORT": env("PGPORT", default=5432),
        "CONN_MAX_AGE": 60,
    }
}
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
SECURE_SSL_REDIRECT = True
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')


from .base import *
import os

DEBUG = True

ALLOWED_HOSTS = ["*"]

import dj_database_url
import os

DATABASES = {
    'default': dj_database_url.config(default='postgres://USER:PASSWORD@HOST:PORT/DBNAME')
}



EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = env('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')


# LOGGING = {
#     "version": 1,
#     "disable_existing_loggers": False,
#     "formatters": {
#         "verbose": {
#             "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
#             "style": "{",
#         },
#         "simple": {
#             "format": "{levelname} {asctime} {message}",
#             "style": "{",
#         },
#     },
#     "filters": {
#         "require_debug_true": {
#             "()": "django.utils.log.RequireDebugTrue",
#         },
#     },
#     "handlers": {
#         "console": {
#             "level": "INFO",
#             "class": "logging.StreamHandler",
#             "formatter": "simple",
#         },
#         "file_error": {
#             "level": "ERROR",
#             "class": "logging.FileHandler",
#             "filename": LOG_DIR / "error.log",
#             "formatter": "verbose",
#         },
#         "file_warning": {
#             "level": "WARNING",
#             "class": "logging.FileHandler",
#             "filename": LOG_DIR / "warning.log",
#             "formatter": "verbose",
#         },
#         "file_info": {
#             "level": "INFO",
#             "class": "logging.FileHandler",
#             "filename": LOG_DIR / "info.log",
#             "formatter": "simple",
#         },
#     },
#     "loggers": {
#         "django": {
#             "handlers": ["console", "file_error"],
#             "level": "INFO",
#             "propagate": False,
#         },
#         "apps.blog": {
#             "handlers": ["console", "file_info", "file_warning", "file_error"],
#             "level": "INFO",
#             "propagate": False,
#         },
#         "apps.users": {
#             "handlers": ["console", "file_info", "file_warning", "file_error"],
#             "level": "INFO",
#             "propagate": False,
#         },
#     },
#     "root": {
#         "handlers": ["console", "file_error"],
#         "level": "INFO",
#     },
# }

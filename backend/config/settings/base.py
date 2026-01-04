import os
import environ
from pathlib import Path
from datetime import timedelta
import dj_database_url

env = environ.Env()
environ.Env.read_env(os.path.join(Path(__file__).resolve().parent.parent.parent, '.env'))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = env('SECRET_KEY', default='django-insecure-super-secret-key-change-in-production')
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEBUG = env.bool('DEBUG', default=False)

ALLOWED_HOSTS = ['*']
CSRF_TRUSTED_ORIGINS = [
    'https://*.railway.app',
    'https://*.up.railway.app',
]
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'drf_spectacular',
    'django_filters',
    # Apps
    'apps.users',
    'apps.channels',
    'apps.vacancies',
    'apps.broadcastprompt',

]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'



AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 6}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

from .cors import *
from .redis import *

JAZZMIN_SETTINGS = {
    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-teal",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "litera",
    "dark_mode_theme": "cyborg",
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-outline-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'JobPulse',
    'VERSION': '1.0.0',
}
from celery.schedules import crontab

# Оптимизированное расписание Celery Beat
CELERY_BEAT_SCHEDULE = {
    # Парсинг вакансий каждые 30 минут (оптимально для HH.ru)
    'parse-hh-vacancies': {
        'task': 'apps.vacancies.tasks.parse_hh_vacancies',
        'schedule': crontab(minute='*/30'),  # Каждые 30 минут
        'options': {
            'expires': 1800,  # Задача истекает через 30 минут
        }
    },

    # Рассылка уведомлений каждые 15 минут
    'notify-new-vacancies': {
        'task': 'apps.vacancies.tasks.notify_users_about_new_vacancies',
        'schedule': crontab(minute='*/15'),
        'options': {
            'expires': 900,
        }
    },

    # Деактивация старых вакансий каждую ночь в 2:00
    'deactivate-old-vacancies': {
        'task': 'apps.vacancies.tasks.deactivate_old_vacancies',
        'schedule': crontab(hour=2, minute=0),
    },

    # Очистка старых логов раз в неделю (понедельник в 3:00)
    'cleanup-old-logs': {
        'task': 'apps.vacancies.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week=1, hour=3, minute=0),
    },

    # Ежедневные уведомления пользователям в 9:00
    'send-daily-notifications': {
        'task': 'apps.users.tasks.send_daily_notifications',
        'schedule': crontab(hour=9, minute=0),
    },

    # Очистка кеша каждую ночь в 00:00
    'clear-cache-midnight': {
        'task': 'apps.users.tasks.clear_expired_cache',
        'schedule': crontab(hour=0, minute=0),
    },

    # Обновление статистики каждый час
    'update-statistics': {
        'task': 'apps.users.tasks.update_user_statistics',
        'schedule': crontab(minute=0),  # Каждый час
    },
}
REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

# Дополнительные настройки Celery для оптимизации
CELERY_TASK_ACKS_LATE = True  # Подтверждать задачу после выполнения
CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Не загружать много задач заранее
CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Повторить при потере worker
CELERY_TASK_ALWAYS_EAGER = False  # Не выполнять синхронно в development
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

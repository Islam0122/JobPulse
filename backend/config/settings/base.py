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
GIGACHAT_CLIENT_ID = env.str('GIGACHAT_CLIENT_ID', default='')
GIGACHAT_SECRET = env.str('GIGACHAT_SECRET', default='')



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
    'apps.review',
    'apps.resume_analysis',

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
USE_I18N = True
USE_L10N = True
TIME_ZONE = "Europe/Istanbul"
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
    'DEFAULT_THROTTLE_CLASSES': [
       'rest_framework.throttling.AnonRateThrottle',
     'rest_framework.throttling.UserRateThrottle'
   ],
     'DEFAULT_THROTTLE_RATES': {
       'anon': '100/hour',
         'user': '1000/hour'
     }
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
    "site_header": "JobPulse",
    "site_brand": "JobPulse",
    "welcome_sign": "Welcome to JobPulse Admin Panel 🚀",
    "copyright": "All Rights Reserved © 2026",

    "topmenu_links": [
        {"name": "Home", "url": "admin:index"},
        {"name": "Users", "model": "users.User"},
        {"name": "Vacancies", "model": "vacancies.Vacancy"},
    ],

    "order_with_respect_to": [
        "users.User",
        "vacancies.Vacancy",
        "vacancies.Stack",
        "vacancies.WorkFormat",
        "vacancies.EmploymentType",
        "broadcastprompt.BroadcastMessage",
        "broadcastprompt.RequiredChannel",
    ],

    "icons": {
        "users.User": "fas fa-user",
        "vacancies.Vacancy": "fas fa-briefcase",
        "vacancies.Stack": "fas fa-laptop-code",
        "vacancies.WorkFormat": "fas fa-building",
        "vacancies.EmploymentType": "fas fa-clock",
        "broadcastprompt.BroadcastMessage": "fas fa-bullhorn",
        "broadcastprompt.RequiredChannel": "fas fa-tv",
    },

    "custom_links": {
        "users": [
            {
                "name": "Аналитика",
                "url": "/admin/analytics/",
                "icon": "fas fa-chart-line",
                "permissions": ["users.view_user"],
            }
        ]
    },

    "show_ui_builder": True,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,
    "brand_colour": False,
    "accent": "accent-navy",
    "navbar": "navbar-white navbar-light",
    "no_navbar_border": False,
    "navbar_fixed": False,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": False,
    "sidebar": "sidebar-dark-info",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "lumen",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-outline-primary",
        "secondary": "btn-outline-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}



SPECTACULAR_SETTINGS = {
    'TITLE': 'JobPulse',
    'VERSION': '1.0.0',
}
from celery.schedules import crontab

# ============= Celery Configuration =============
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Базовые настройки
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Таймауты и лимиты
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 минут
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 минут
CELERY_RESULT_EXPIRES = 3600  # 1 час

# Сериализация
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']

CELERY_ENABLE_UTC = True
CELERY_TIMEZONE = "Europe/Istanbul"

# ============= API Rate Limits =============
HH_API_RATE_LIMIT = 150  # запросов в минуту
HH_API_MIN_INTERVAL = 0.5  # секунд между запросами
DEVKG_API_RATE_LIMIT = 60  # запросов в минуту
DEVKG_API_MIN_INTERVAL = 1.0  # секунд между запросами

# ============= Оптимизированное расписание Celery Beat =============
CELERY_BEAT_SCHEDULE = {
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📥 ПАРСИНГ ВАКАНСИЙ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # HH.ru - каждые 2 часа (рабочее время)
    'parse-hh-vacancies': {
        'task': 'apps.vacancies.tasks.parse_hh_vacancies',
        'schedule': crontab(
            minute=0,
            hour='8-20/2'  # 8:00, 10:00, 12:00, 14:00, 16:00, 18:00, 20:00
        ),
        'options': {
            'queue': 'parsing',
            'priority': 5,
        }
    },


    # Dev.kg - каждые 4 часа
    'parse-devkg-vacancies': {
        'task': 'apps.vacancies.tasks.parse_devkg_vacancies',
        'schedule': crontab(
            minute=30,
            hour='9-21/4'  # 9:30, 13:30, 17:30, 21:30
        ),
        'kwargs': {'max_pages': 3},
        'options': {
            'queue': 'parsing',
            'priority': 5,
        }
    },
    # Telegram
    'parse-telegram-vacancies': {
        'task': 'apps.vacancies.tasks.parse_telegram_vacancies',
        'schedule': crontab(
            minute=15,
            hour='*/6'  # 00:15, 06:15, 12:15, 18:15
        ),
        'options': {
            'queue': 'parsing',
            'priority': 5,
        }
    },
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📨 УВЕДОМЛЕНИЯ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Уведомления о новых вакансиях - каждые 20 минут (рабочее время)
    'notify-new-vacancies': {
        'task': 'apps.vacancies.tasks.notify_users_about_new_vacancies',
        'schedule': crontab(
            minute='*/20',
            hour='8-22'  # С 8:00 до 22:00
        ),
        'options': {
            'queue': 'notifications',
            'priority': 7,
        }
    },

    # Ежедневные уведомления пользователям в 9:00
    'send-daily-notifications': {
        'task': 'apps.users.tasks.send_daily_notifications',
        'schedule': crontab(hour=9, minute=0),
        'options': {
            'queue': 'notifications',
            'priority': 6,
        }
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🧹 ОБСЛУЖИВАНИЕ
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Деактивация старых вакансий - каждую ночь в 2:00
    'deactivate-old-vacancies': {
        'task': 'apps.vacancies.tasks.deactivate_old_vacancies',
        'schedule': crontab(hour=2, minute=0),
        'options': {
            'queue': 'maintenance',
            'priority': 3,
        }
    },

    # Очистка старых логов - каждое воскресенье в 3:00
    'cleanup-old-logs': {
        'task': 'apps.vacancies.tasks.cleanup_old_logs',
        'schedule': crontab(day_of_week=0, hour=3, minute=0),
        'options': {
            'queue': 'maintenance',
            'priority': 2,
        }
    },

    # Очистка кеша - каждую ночь в 00:00
    'clear-cache-midnight': {
        'task': 'apps.users.tasks.clear_expired_cache',
        'schedule': crontab(hour=0, minute=0),
        'options': {
            'queue': 'maintenance',
            'priority': 3,
        }
    },

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📊 СТАТИСТИКА
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # Обновление статистики - каждый час
    'update-statistics': {
        'task': 'apps.users.tasks.update_user_statistics',
        'schedule': crontab(minute=0),
        'options': {
            'queue': 'statistics',
            'priority': 4,
        }
    },
}

CELERY_TASK_ROUTES = {
    # Парсинг
    'apps.vacancies.tasks.parse_hh_vacancies': {'queue': 'parsing'},
    'apps.vacancies.tasks.parse_devkg_vacancies': {'queue': 'parsing'},
    'apps.vacancies.tasks.parse_all_sources': {'queue': 'parsing'},

    # Уведомления
    'apps.vacancies.tasks.notify_users_about_new_vacancies': {'queue': 'notifications'},
    'apps.users.tasks.send_daily_notifications': {'queue': 'notifications'},

    # Обслуживание
    'apps.vacancies.tasks.deactivate_old_vacancies': {'queue': 'maintenance'},
    'apps.vacancies.tasks.cleanup_old_logs': {'queue': 'maintenance'},
    'apps.users.tasks.clear_expired_cache': {'queue': 'maintenance'},

    # Статистика
    'apps.users.tasks.update_user_statistics': {'queue': 'statistics'},
}

CELERY_TASK_DEFAULT_QUEUE = 'maintenance'
CELERY_TASK_DEFAULT_EXCHANGE = 'default'
CELERY_TASK_DEFAULT_ROUTING_KEY = 'maintenance'


CELERY_TASK_QUEUE_PRIORITIES = {
    'notifications': 7,
    'parsing': 5,
    'statistics': 4,
    'maintenance': 2,
    'default': 1,
}

CELERY_WORKER_HIJACK_ROOT_LOGGER = False
CELERY_WORKER_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s] %(message)s'
CELERY_WORKER_TASK_LOG_FORMAT = '[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s'
CELERY_WORKER_SEND_TASK_EVENTS = True
CELERY_TASK_SEND_SENT_EVENT = True
CELERY_TRACK_STARTED = True
CELERY_TASK_AUTORETRY_FOR = (TimeoutError, ConnectionError)
CELERY_TASK_MAX_RETRIES = 3
CELERY_TASK_DEFAULT_RETRY_DELAY = 60  # 1 минута
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

from .telethon import *

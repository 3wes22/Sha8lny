"""
Django base settings for Sha8alny project.

This file contains settings common to all environments.
Environment-specific settings should go in development.py or production.py
"""

import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-CHANGE-THIS-IN-PRODUCTION')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1', cast=lambda v: [s.strip() for s in v.split(',')])


# Application definition

DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # For JWT token blacklisting on logout
    'corsheaders',
    'drf_spectacular',  # API documentation (OpenAPI/Swagger)
]

LOCAL_APPS = [
    'apps.core',
    'apps.users',
    'apps.assessments',
    'apps.roadmaps',
    'apps.courses',
    'apps.advisory',
    'apps.jobs',
    'apps.progress',
    'apps.career_tools',
    'apps.notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware (should be before CommonMiddleware)
    'django.contrib.sessions.middleware.SessionMiddleware',
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


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME', default='sha8alny_db'),
        'USER': config('DB_USER', default='postgres'),
        'PASSWORD': config('DB_PASSWORD', default='postgres'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Africa/Cairo'  # Egypt timezone

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files (User uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model (to be created in apps.users)
AUTH_USER_MODEL = 'users.User'  # Uncomment after creating custom User model


# Django REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',  # For development API browsing
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',  # For API documentation
    'EXCEPTION_HANDLER': 'apps.core.exceptions.custom_exception_handler',
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DEFAULT_THROTTLE_RATES': {
        'ai_burst': '3/min',
        'ai_sustained': '20/hour',
    },
}


# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}


# CORS Configuration
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda v: [s.strip() for s in v.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


# Cache Configuration
DJANGO_CACHE_BACKEND = config(
    'DJANGO_CACHE_BACKEND',
    default='django.core.cache.backends.locmem.LocMemCache',
)
DJANGO_CACHE_LOCATION = config('DJANGO_CACHE_LOCATION', default='sha8alny-cache')

CACHES = {
    'default': {
        'BACKEND': DJANGO_CACHE_BACKEND,
        'KEY_PREFIX': 'sha8alny',
        'TIMEOUT': 300,
    }
}

if DJANGO_CACHE_BACKEND == 'django.core.cache.backends.redis.RedisCache':
    CACHES['default']['LOCATION'] = config('REDIS_URL', default='redis://127.0.0.1:6379/1')
    CACHES['default']['OPTIONS'] = {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
    }
elif DJANGO_CACHE_BACKEND == 'django.core.cache.backends.locmem.LocMemCache':
    CACHES['default']['LOCATION'] = DJANGO_CACHE_LOCATION
elif DJANGO_CACHE_LOCATION:
    CACHES['default']['LOCATION'] = DJANGO_CACHE_LOCATION


# Celery Configuration
CELERY_BROKER_URL = config('CELERY_BROKER_URL', default='redis://127.0.0.1:6379/0')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND', default='redis://127.0.0.1:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 120

# ---------------------------------------------------------------------------
# AI Worker Queue — ADR-001: single-lane by design
# ---------------------------------------------------------------------------
# GPU can only handle one inference at a time on M1 16GB / RTX 3050.
# Route all AI tasks to a dedicated queue consumed by a single-concurrency worker.
#
# Start the AI worker with:
#   celery -A config worker -Q ai --concurrency=1 --max-tasks-per-child=50 -n ai@%h
#
# Start the default worker (non-AI tasks) separately:
#   celery -A config worker -Q default --concurrency=4 -n default@%h
# ---------------------------------------------------------------------------
from apps.core.ai_settings import (  # noqa: E402
    AI_CELERY_QUEUE,
    AI_TASK_SOFT_TIME_LIMIT,
    AI_TASK_HARD_TIME_LIMIT,
)

CELERY_TASK_ROUTES = {
    'apps.assessments.tasks.*': {'queue': AI_CELERY_QUEUE},
    'apps.roadmaps.tasks.*': {'queue': AI_CELERY_QUEUE},
    'apps.advisory.tasks.*': {'queue': AI_CELERY_QUEUE},
}

CELERY_TASK_DEFAULT_QUEUE = 'default'
CELERY_TASK_SOFT_TIME_LIMIT = AI_TASK_SOFT_TIME_LIMIT
CELERY_TASK_TIME_LIMIT = AI_TASK_HARD_TIME_LIMIT


# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
        'apps': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}


# Security Settings (will be overridden in production)
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True


# ---------------------------------------------------------------------------
# AI/LLM Configuration — Hosted Gemini default with provider abstraction
# ---------------------------------------------------------------------------
# All AI runtime settings (provider selection, Gemini models, retries, optional
# Ollama fallback, queue config) live in:
#   apps/core/ai_settings.py
# Import from there in any module that needs AI configuration.


# External API Configuration
UDEMY_CLIENT_ID = config('UDEMY_CLIENT_ID', default='')
UDEMY_CLIENT_SECRET = config('UDEMY_CLIENT_SECRET', default='')
YOUTUBE_API_KEY = config('YOUTUBE_API_KEY', default='')


# Auth0 Configuration
AUTH0_DOMAIN = config('AUTH0_DOMAIN', default='')
AUTH0_CLIENT_ID = config('AUTH0_CLIENT_ID', default='')
AUTH0_CLIENT_SECRET = config('AUTH0_CLIENT_SECRET', default='')
AUTH0_AUDIENCE = config('AUTH0_AUDIENCE', default='')


# drf-spectacular Configuration (OpenAPI/Swagger)
SPECTACULAR_SETTINGS = {
    'TITLE': 'Sha8alny API',
    'DESCRIPTION': 'AI-powered career development platform API',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': r'/api/v1/',
    # Use CDN for Swagger UI assets (no sidecar package needed)
    'SWAGGER_UI_DIST': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest',
    'SWAGGER_UI_FAVICON_HREF': 'https://cdn.jsdelivr.net/npm/swagger-ui-dist@latest/favicon-32x32.png',
}

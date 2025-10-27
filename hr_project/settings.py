import os
from pathlib import Path
from datetime import timedelta

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'change-me-in-prod')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Project apps
    'apps.employees',
    'apps.authentication',
    'apps.roles',
    'apps.admin_dashboard',
    'apps.leaves',
    'apps.notifications',
    'apps.documents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Redirect anonymous users to login for protected pages
    'hr_project.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hr_project.urls'

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
                'apps.notifications.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'hr_project.wsgi.application'
ASGI_APPLICATION = 'hr_project.asgi.application'

# Database (MySQL if env vars set; otherwise SQLite for dev)
if os.getenv('MYSQL_DATABASE'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('MYSQL_DATABASE'),
            'USER': os.getenv('MYSQL_USER'),
            'PASSWORD': os.getenv('MYSQL_PASSWORD'),
            'HOST': os.getenv('MYSQL_HOST', 'localhost'),
            'PORT': os.getenv('MYSQL_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
            # Connection pooling for performance under load
            'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
            'CONN_HEALTH_CHECKS': True,  # Check connection health before reusing
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Redis Cache Configuration with async support and connection pooling
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
                'socket_keepalive': True,
                'socket_timeout': 5,
                'socket_connect_timeout': 5,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
        },
        'KEY_PREFIX': 'hr_app',
        'TIMEOUT': 300,  # Default timeout: 5 minutes
    }
}

# Cache middleware (optional - for whole page caching)
# MIDDLEWARE = [
#     'django.middleware.cache.UpdateCacheMiddleware',
#     ...other middleware...
#     'django.middleware.cache.FetchFromCacheMiddleware',
# ]

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth redirects
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/accounts/login/'

# Allow authentication by username or email
AUTHENTICATION_BACKENDS = [
    'apps.authentication.backends.EmailOrUsernameModelBackend',
    'django.contrib.auth.backends.ModelBackend',
]

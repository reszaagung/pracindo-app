"""
Django settings — pracindo_erp
Django 5.2 · PostgreSQL · DRF Token (ExpiringTokenAuthentication)

Semua rahasia dibaca dari .env. Jangan pernah menaruh nilai asli di file ini.
"""

import os
BUKA_API = os.environ.get('BUKA_API') == '1'
from pathlib import Path

from dotenv import load_dotenv

# =========================================================
# PATH & ENV
# =========================================================
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


def env_bool(nama, default='False'):
    return os.getenv(nama, default).strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(nama, default=''):
    raw = os.getenv(nama, default)
    return [x.strip() for x in raw.split(',') if x.strip()]


# =========================================================
# KEAMANAN DASAR
# =========================================================
SECRET_KEY = os.getenv('SECRET_KEY')
if not SECRET_KEY:
    raise RuntimeError(
        'SECRET_KEY belum diset di .env. '
        'Generate dengan: python -c "from django.core.management.utils import '
        'get_random_secret_key; print(get_random_secret_key())"'
    )

DEBUG = env_bool('DEBUG', 'False')

ALLOWED_HOSTS = env_list('ALLOWED_HOSTS') or [
    '31.97.221.43',
    'pracindo-marshitek.company',
    'www.pracindo-marshitek.company',
    'localhost',
    '127.0.0.1',
    'testserver',          
]


# =========================================================
# APLIKASI
# =========================================================
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
    'rest_framework.authtoken',
    'corsheaders',
    'django_filters',
    'drf_spectacular',
]

LOCAL_APPS = [
    # Lapis 1 — fondasi, tidak mengimpor app lokal lain
    'core',
    'staff_user',

    # Lapis 2 — master data & infrastruktur generik
    'master',
    'dokumen',

    # Lapis 3
    'inventory',

    # Lapis 4 — domain (kelompok sejajar, boleh saling panggil di dalam fungsi)
    'akunting',
    'keuangan',
    'pajak',
    'warehouse',
    'produksi',
    'sales_order',
    'logistik',
    'work_order',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS 

AUTH_USER_MODEL = 'staff_user.Profil'


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    #'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'pracindo_erp.urls'
WSGI_APPLICATION = 'pracindo_erp.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


DATABASES = {
    'default': {
        'ENGINE':   os.getenv('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME':     os.getenv('DB_NAME', 'pracindo_dbms'),
        'USER':     os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST':     os.getenv('DB_HOST', '127.0.0.1'),
        'PORT':     os.getenv('DB_PORT', '5432'),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
        'OPTIONS': {'connect_timeout': 10},
    }
}
PGCRYPTO_KEY = os.getenv('DB_ENCRYPTION_KEY', 'SECRET_KEY')
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


REST_FRAMEWORK = {

    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework.authentication.SessionAuthentication',
        'staff_user.authentication.ExpiringTokenAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    'DATETIME_FORMAT': '%Y-%m-%d %H:%M:%S',
    'DATE_FORMAT': '%Y-%m-%d',
    'COERCE_DECIMAL_TO_STRING': True,   
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'API Sistem Pracindo',
    'DESCRIPTION': 'Dokumentasi jalur API untuk sistem ERP.',
    'VERSION': '1.0.0',
}

TOKEN_EXPIRE_HOURS = int(os.getenv('TOKEN_EXPIRE_HOURS', '12'))


CORS_ALLOW_CREDENTIALS = True
CORS_ALLOWED_ORIGINS = env_list('CORS_ALLOWED_ORIGINS') or [
    'https://pracindo-marshitek.company',
    'https://www.pracindo-marshitek.company',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

CSRF_TRUSTED_ORIGINS = env_list('CSRF_TRUSTED_ORIGINS') or [
    'https://pracindo-marshitek.company',
    'https://www.pracindo-marshitek.company',
    'http://localhost:5173',     
    'http://127.0.0.1:5173',
]


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
     'OPTIONS': {'min_length': 10}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Jakarta'

USE_I18N = True
USE_TZ = True
USE_THOUSAND_SEPARATOR = True



STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static'] if (BASE_DIR / 'static').exists() else []

MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', BASE_DIR / 'media'))
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

STORAGES = {
    'default': {
        'BACKEND': 'django.core.files.storage.FileSystemStorage',
    },
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024


if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'


LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'ringkas': {
            'format': '{asctime} {levelname} {name} · {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'ringkas',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'pracindo.log',
            'maxBytes': 5 * 1024 * 1024,
            'backupCount': 5,
            'formatter': 'ringkas',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO' if not DEBUG else 'DEBUG',
    },
    'loggers': {
        'django.db.backends': {
            'level': 'WARNING',      #
            'propagate': False,
            'handlers': ['console'],
        },
        # Semua posting jurnal dan mutasi kas lewat sini.
        'akunting': {'level': 'INFO', 'propagate': True},
        'keuangan': {'level': 'INFO', 'propagate': True},
    },
}
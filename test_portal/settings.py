import os
from pathlib import Path
from dotenv import load_dotenv
import dj_database_url

# ─── Load .env ───────────────────────────────────────────────────────────────
load_dotenv()

# ─── Paths ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# ─── Security ────────────────────────────────────────────────────────────────
SECRET_KEY   = os.getenv('SECRET_KEY', 'unsafe-default-for-dev')
DEBUG        = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')
ALLOWED_HOSTS = [
    'petroxtestbackend.onrender.com',
    'localhost',
    '127.0.0.1'
]
# ─── Applications ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third‑party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'channels',
    'storages',

    # Your apps
    'exams',
]

# ─── Middleware ──────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',              # CORS first
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ─── URLs & WSGI/ASGI ────────────────────────────────────────────────────────
ROOT_URLCONF = 'test_portal.urls'
WSGI_APPLICATION = 'test_portal.wsgi.application'
ASGI_APPLICATION = 'test_portal.asgi.application'

# ─── Database ────────────────────────────────────────────────────────────────
# Expect DATABASE_URL like:
#   postgres://user:pass@host:port/dbname?sslmode=require
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {
        'default': dj_database_url.config(
            default=os.getenv('DATABASE_URL'),
            conn_max_age=600,
            ssl_require=True,
        )
    }

# ─── REST Framework & JWT ───────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}

# ─── CORS ───────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = True   # tighten in prod
CORS_ALLOW_METHODS = [
    'DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type',
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with',
]

# ─── Static & Media ─────────────────────────────────────────────────────────
STATIC_URL   = '/static/'
STATIC_ROOT  = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Google Cloud Storage for media
GCS_CREDENTIALS_PATH = r'test_portal/MY_CREDENTAIL.JSON'
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS_PATH
GOOGLE_APPLICATION_CREDENTIALS = GCS_CREDENTIALS_PATH
GS_BUCKET_NAME         = 'petrox-materials'
# GCS_CREDENTIALS_PATH   = os.getenv('GCS_CREDENTIALS_PATH')  # point this in your env
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = GCS_CREDENTIALS_PATH
DEFAULT_FILE_STORAGE   = 'storages.backends.gcloud.GoogleCloudStorage'
MEDIA_URL              = f'https://storage.googleapis.com/{GS_BUCKET_NAME}/'
GS_DEFAULT_ACL         = None

# ─── Channels ────────────────────────────────────────────────────────────────
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    }
}

# ─── Internationalization ────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE     = 'UTC'
USE_I18N      = True
USE_TZ        = True

# ─── Email ──────────────────────────────────────────────────────────────────
EMAIL_BACKEND    = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST       = 'smtp.gmail.com'
EMAIL_PORT       = 465
EMAIL_USE_TLS    = False
EMAIL_USE_SSL    = True
EMAIL_HOST_USER = 'thecbsteam8@gmail.com'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL  = 'Petrox Assessment <thecbsteam8@gmail.com>'

# Link back to your React frontend
FRONTEND_DOMAIN = os.getenv('FRONTEND_DOMAIN', 'http://localhost:3000')

# ─── Production Security Enhancements ───────────────────────────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT       = True
    SESSION_COOKIE_SECURE     = True
    CSRF_COOKIE_SECURE        = True
    SECURE_PROXY_SSL_HEADER   = ('HTTP_X_FORWARDED_PROTO', 'https')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

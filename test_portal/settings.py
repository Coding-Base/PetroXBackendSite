import os
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv
from datetime import timedelta

# corsheaders defaults
from corsheaders.defaults import default_headers, default_methods

# Load environment variables
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-secret-key")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG", "False") == "True"

# FIXED: Dynamic allowed hosts with Render support
allowed_hosts_str = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,petroxtestbackend.onrender.com")
ALLOWED_HOSTS = [host.strip() for host in allowed_hosts_str.split(",")]
EMAIL_BATCH_SIZE = int(os.getenv("EMAIL_BATCH_SIZE", 20))        # default is 20
EMAIL_BATCH_PAUSE = float(os.getenv("EMAIL_BATCH_PAUSE", 0.5))  # seconds to sleep between batches

# Automatically add Render's hostname
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    if RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    'corsheaders',  # Make sure this is above all your own apps
    'rest_framework',
    'rest_framework_simplejwt',
    'anymail',      # Anymail for SendGrid / transactional email APIs
    'channels',
    'storages',                # keep if you still use django-storages elsewhere
    'exams',
    # Cloudinary Django integration
    'cloudinary',
    'cloudinary_storage',
    'updates',
   
]

# --------------------------
# CORS Configuration (explicit & robust)
# --------------------------
# For production prefer explicit origins instead of allowing all
CORS_ALLOW_ALL_ORIGINS = False
FRONTEND_DOMAIN = os.getenv('FRONTEND_DOMAIN', 'http://localhost:3000')
CORS_ALLOWED_ORIGINS = [
    "https://petrox-test-frontend.onrender.com",
    "https://petroxtestbackend.onrender.com",   # if needed
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# If you do not use cookie/session auth from the browser, leave this False
# (you're using Bearer tokens which don't require cookies)
CORS_ALLOW_CREDENTIALS = False

# Keep default methods and headers, and append any custom ones you need
CORS_ALLOW_METHODS = list(default_methods)  # includes OPTIONS, GET, POST, PUT, PATCH, DELETE, HEAD

CORS_ALLOW_HEADERS = list(default_headers) + [
    'authorization',      # ensure Authorization header is allowed
    'content-type',       # usually present in default_headers but duplicated is fine
    'x-upload-timeout',   # your custom header seen in the request
    # add any other custom headers you use
]

# Optional: expose headers (useful if you need to read custom response headers)
CORS_EXPOSE_HEADERS = [
    'Content-Disposition',
    'x-total-count',
]

# --------------------------
# Middleware (CorsMiddleware must be early)
# --------------------------
MIDDLEWARE = [
    "core.middleware.force_cors_echo.ForceCORSEchoMiddleware",
    "corsheaders.middleware.CorsMiddleware",  # Must be at the top!
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

ROOT_URLCONF = "test_portal.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "test_portal.wsgi.application"
ASGI_APPLICATION = "test_portal.asgi.application"

# Database
DATABASES = {
    "default": dj_database_url.config(
        default=os.getenv("DATABASE_URL"),
        conn_max_age=600,
        ssl_require=not DEBUG
    )
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        # keep session auth if you want the browsable API to work with login sessions:
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}
# Static files
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ---------------------------
# Cloudinary configuration
# ---------------------------
# You can set either individual vars below OR a single CLOUDINARY_URL env var
# CLOUDINARY_URL example: cloudinary://API_KEY:API_SECRET@CLOUD_NAME
CLOUDINARY_STORAGE = {
    "CLOUD_NAME": os.getenv("CLOUDINARY_CLOUD_NAME", ""),
    "API_KEY": os.getenv("CLOUDINARY_API_KEY", ""),
    "API_SECRET": os.getenv("CLOUDINARY_API_SECRET", ""),
    # 'RESOURCE_TYPE': 'auto'  # default is 'auto'; for raw files Cloudinary will store as raw
}
CLOUDINARY_MAX_UPLOAD_BYTES = int(os.getenv("CLOUDINARY_MAX_UPLOAD_BYTES", 10 * 1024 * 1024))
CLOUDINARY = {
    "cloud_name": CLOUDINARY_STORAGE.get("CLOUD_NAME", "") or os.getenv("CLOUDINARY_CLOUD_NAME", ""),
}
# Use RawMediaCloudinaryStorage so PDFs / documents are uploaded as raw resources
DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.RawMediaCloudinaryStorage"
# If you prefer images as default, change to:
# DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"

# Google Cloud credentials from Render (keep if you still use GCS elsewhere)
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Security settings
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [
        "https://petroxtestbackend.onrender.com",
        "https://petrox-test-frontend.onrender.com"
    ]

# Ensure this is not set to a restrictive value that breaks requests
SECURE_CROSS_ORIGIN_OPENER_POLICY = None

# ---------------------------
# EMAIL / SendGrid via Anymail (preferred for Render - uses HTTP API)
# ---------------------------
# Toggle use with env var: set USE_SENDGRID=True in Render secrets to enable SendGrid
USE_SENDGRID = os.getenv("USE_SENDGRID", "True") == "True"

# Default "from" sender (keep as you used)
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Petrox Assessment <thecbsteam8@gmail.com>")

if USE_SENDGRID:
    # Use django-anymail + SendGrid HTTP API
    EMAIL_BACKEND = "anymail.backends.sendgrid.EmailBackend"
    ANYMAIL = {
        "SENDGRID_API_KEY": os.getenv("SENDGRID_API_KEY", ""),  # set this in Render secrets
    }
    # Optional: a short timeout for API calls
    EMAIL_TIMEOUT = int(os.getenv("EMAIL_TIMEOUT", 10))
else:
    # Fallback: SMTP (useful for local dev if you prefer)
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True") == "True"
    EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL", "False") == "True"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "thecbsteam8@gmail.com")
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_PASSWORD', "")

# Channels configuration (if using WebSockets)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}



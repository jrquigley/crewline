import os
import secrets
import sys
from pathlib import Path
from urllib.parse import urlsplit
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
TESTING = 'test' in sys.argv
DATA_DIR = Path(os.environ.get('DATA_DIR', BASE_DIR / '.local'))
DATA_DIR.mkdir(parents=True, exist_ok=True)
DEBUG = False
APP_BASE_URL = os.environ.get('APP_BASE_URL', 'https://shifts.quigspace.com').rstrip('/')
origin = urlsplit(APP_BASE_URL)
LOCAL_HTTP = os.environ.get('ALLOW_INSECURE_HTTP', '').lower() == 'true' or TESTING
if origin.scheme not in ('http', 'https') or not origin.hostname or origin.username or origin.path not in ('', '/'):
    raise ImproperlyConfigured('APP_BASE_URL must be an http(s) origin without a path or credentials.')
if origin.scheme != 'https' and not LOCAL_HTTP:
    raise ImproperlyConfigured('HTTPS is required. ALLOW_INSECURE_HTTP=true is only for isolated local testing.')
secret_path = DATA_DIR / 'secret.key'
if os.environ.get('DJANGO_SECRET_KEY'):
    SECRET_KEY = os.environ['DJANGO_SECRET_KEY']
elif TESTING:
    SECRET_KEY = 'test-only-' + 'randomness-not-used-outside-the-test-run-' * 2
else:
    if not secret_path.exists():
        try:
            with secret_path.open('x', encoding='utf-8') as f:
                f.write(secrets.token_urlsafe(64))
            secret_path.chmod(0o600)
        except FileExistsError:
            pass
    SECRET_KEY = secret_path.read_text().strip()
if len(SECRET_KEY) < 50:
    raise ImproperlyConfigured('DJANGO_SECRET_KEY must contain at least 50 random characters.')
ALLOWED_HOSTS = [origin.hostname, 'localhost', '127.0.0.1'] + (['testserver'] if TESTING else [])
CSRF_TRUSTED_ORIGINS = [APP_BASE_URL]
INSTALLED_APPS = ['django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
                  'django.contrib.messages', 'django.contrib.staticfiles', 'scheduling']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware', 'whitenoise.middleware.WhiteNoiseMiddleware',
              'django.contrib.sessions.middleware.SessionMiddleware', 'django.middleware.common.CommonMiddleware',
              'django.middleware.csrf.CsrfViewMiddleware', 'django.contrib.auth.middleware.AuthenticationMiddleware',
              'scheduling.middleware.AccessMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
              'django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND': 'django.template.backends.django.DjangoTemplates', 'DIRS': [BASE_DIR / 'templates'],
              'APP_DIRS': True, 'OPTIONS': {'context_processors': ['django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth', 'django.contrib.messages.context_processors.messages',
                'scheduling.context.navigation']}}]
WSGI_APPLICATION = 'config.wsgi.application'
DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': DATA_DIR / 'crewline.sqlite3',
                        'OPTIONS': {'timeout': 20, 'transaction_mode': 'IMMEDIATE'},
                        'TEST': {'NAME': DATA_DIR / 'test-crewline.sqlite3'}}}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 15}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
SESSION_COOKIE_SECURE = not LOCAL_HTTP
CSRF_COOKIE_SECURE = not LOCAL_HTTP
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 12 * 60 * 60
SECURE_SSL_REDIRECT = not LOCAL_HTTP
SECURE_REDIRECT_EXEMPT = [r'^healthz/$']
SECURE_HSTS_SECONDS = 31536000 if not LOCAL_HTTP else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'
CSRF_FAILURE_VIEW = 'scheduling.views.csrf_failure'
if os.environ.get('TRUST_PROXY', '').lower() == 'true':
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
TIME_ZONE = os.environ.get('SCHEDULING_TIMEZONE', 'America/Los_Angeles')
USE_TZ = True
LANGUAGE_CODE = 'en-us'
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
STORAGES = {'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
            'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage'}}
DATA_UPLOAD_MAX_MEMORY_SIZE = 64 * 1024
DATA_UPLOAD_MAX_NUMBER_FIELDS = 150
EMAIL_HOST = os.environ.get('SMTP_HOST', '')
EMAIL_PORT = int(os.environ.get('SMTP_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('SMTP_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
EMAIL_USE_TLS = os.environ.get('SMTP_TLS', 'true').lower() == 'true'
EMAIL_USE_SSL = os.environ.get('SMTP_SSL', 'false').lower() == 'true'
if EMAIL_USE_TLS and EMAIL_USE_SSL:
    raise ImproperlyConfigured('Use SMTP_TLS or SMTP_SSL, not both.')
EMAIL_TIMEOUT = 20
DEFAULT_FROM_EMAIL = os.environ.get('SMTP_FROM', 'Crewline <schedule@quigspace.com>')
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
SMTP_CONFIGURED = bool(EMAIL_HOST)
PASSWORD_RESET_TIMEOUT = 3600
LOGGING = {'version': 1, 'disable_existing_loggers': False,
           'filters': {'private_urls': {'()': 'scheduling.safe_logging.PrivateURLFilter'}},
           'handlers': {'console': {'class': 'logging.StreamHandler', 'filters': ['private_urls']}},
           'loggers': {'django.security': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
                       'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False}}}

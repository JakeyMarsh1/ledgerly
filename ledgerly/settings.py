"""
Core configuration module for the Ledgerly Django project.

Every section below is annotated so you can quickly understand what it
does and decide whether to keep or adjust it for your deployment.
"""

from pathlib import Path
import os
import dj_database_url

# BASE_DIR will be reused throughout this file to build project-relative
# paths (for example, when pointing at the templates directory below).


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!

try:
    # Pull secrets and database configuration from env.py locally,
    # falling back to environment variables in deployed environments.
    from env import SECRET_KEY, DATABASE_URL  # type: ignore
except ImportError:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    DATABASE_URL = os.environ.get("DATABASE_URL")

# SECURITY WARNING: don't run with debug turned on in production!
# Toggle Django debug features. Set to False when deploying to
# production environments.
DEBUG = True

# Hosts/domain names that this Django site can serve.
ALLOWED_HOSTS = [
    '127.0.0.1',
    'localhost',
    'ledgerly-90931141abd8.herokuapp.com',
]

# Allow CSRF validation to trust requests originating from these
# domains. Useful for Heroku-hosted environments.
CSRF_TRUSTED_ORIGINS = ['https://*.herokuapp.com']


# Application definition

# Core Django + third-party apps that power the project.
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'whitenoise.runserver_nostatic',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'expenses',
]

# Update deprecated allauth settings
ACCOUNT_LOGIN_METHODS = {'username'}
ACCOUNT_SIGNUP_FIELDS = ['email', 'username*', 'password1*', 'password2*']

# Use the allauth authentication backend so case-insensitive username
# matching is respected during login, while keeping Django's defaults.
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

MIDDLEWARE = [
    # Adds security-related HTTP headers.
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # Manages session data stored in cookies or the DB.
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Keeps user account data in sync for django-allauth.
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ledgerly.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # Point Django to your custom templates (e.g. overridden
        # django-allauth forms).
        'DIRS': [BASE_DIR / 'expenses' / 'templates'],
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

WSGI_APPLICATION = 'ledgerly.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    # dj_database_url reads DATABASE_URL (from env.py or environment).
    # Falls back to local SQLite only if no database URL is supplied.
    'default': dj_database_url.config(
        default=(DATABASE_URL or f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600,
        ssl_require=not DEBUG,
    )
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

# Validators run whenever a user sets or changes a password. They help
# enforce strong password policies out of the box.
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'UserAttributeSimilarityValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'MinimumLengthValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'CommonPasswordValidator'
        ),
    },
    {
        'NAME': (
            'django.contrib.auth.password_validation.'
            'NumericPasswordValidator'
        ),
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

# Default locale/timezone configuration. Adjust to match your primary
# audience or hosting region.
LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

# URL prefix where static assets are served from (collectstatic also
# publishes here when you deploy).
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
if DEBUG:
    STATICFILES_STORAGE = (
        'django.contrib.staticfiles.storage.StaticFilesStorage'
    )
else:
    STATICFILES_STORAGE = (
        'whitenoise.storage.CompressedManifestStaticFilesStorage'
    )
STATICFILES_DIRS = [
    BASE_DIR / "assets" / "images",
]

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Configure django-crispy-forms to output Bootstrap 5 markup.
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Required by django-allauth's sites framework integration.
SITE_ID = 1

# Post-login and login-required redirect destinations.
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'

# Email configuration: default to logging emails to the console so optional
# address submission on signup does not crash when no SMTP service is
# configured (e.g., on Heroku free tiers). Override via environment vars when
# a real email provider is available.
EMAIL_BACKEND = os.environ.get(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = os.environ.get(
    "DEFAULT_FROM_EMAIL",
    "Ledgerly <no-reply@ledgerly.app>",
)


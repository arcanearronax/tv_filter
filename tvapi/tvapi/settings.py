"""
    tvapi.settings
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get("SKEY")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = [os.environ.get("HostName")]


# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "tvapi.apps.TVAPIConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "tvapi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = "tvapi.wsgi.application"

DATABASES = {  # https://docs.djangoproject.com/en/2.2/ref/settings/#databases
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "tvapi",
        "USER": os.environ.get("UserName"),
        "PASSWORD": os.environ.get("UserPass"),
        "HOST": "localhost",
        "PORT": "",
    }
}

AUTH_PASSWORD_VALIDATORS = [  # https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",},
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "US/Eastern"

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = "/static/"  # This is the uri_path for static file requests
STATIC_ROOT = "/var/www/html/django/"  # This is the path for production static files
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static"),
)  # This is the path for dev static files

# Custom logging for the project
LOGHOME = os.environ["LogHome"]  # This identifies the path for app log files
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{asctime}-{thread:d}-{module}.{funcName}: {message}",
            "style": "{",
        },
        "verbose": {
            "format": "{asctime}-{levelname}-{process:d}-{thread:d}-{module}.{funcName}: {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "simple",},
        "apifile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "{}/scraper.log".format(LOGHOME),
            "formatter": "simple",
        },
        "modelfile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "{}/model.log".format(LOGHOME),
            "formatter": "simple",
        },
        "viewfile": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "{}/view.log".format(LOGHOME),
            "formatter": "simple",
        },
    },
    "loggers": {
        "apilog": {  # logs api request info
            "handlers": ["apifile", "console"],
            "level": "DEBUG",
            "propogate": True,
        },
        "modellog": {  # logs model processing info
            "handlers": ["modelfile", "console"],
            "level": "DEBUG",
            "propogate": True,
        },
        "viewlog": {  # logs view processing info
            "handlers": ["viewfile", "console"],
            "level": "DEBUG",
            "propogate": True,
        },
    },
}

from __future__ import annotations

import os
from pathlib import Path
import logging

from django.db.backends.signals import connection_created
from django.dispatch import receiver

VIBE_SQLITE_LOGGER = "vibe.sqlite"
logger = logging.getLogger(VIBE_SQLITE_LOGGER)

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "replace-me-in-production"
DEBUG = True
ALLOWED_HOSTS: list[str] = [
    host.strip()
    for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
if not ALLOWED_HOSTS and DEBUG:
    ALLOWED_HOSTS = ["localhost", "127.0.0.1", "[::1]", "testserver"]

INSTALLED_APPS = [
    "config.apps.CoreConfig",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "crispy_forms",
    "tailwind",
    "django_htmx",
    "mptt",
    "theme",
    "accounts",
    "notices",
    "posts",
    "events",
    "polls",
    "surveys",
    "admin_dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
]

ROOT_URLCONF = "config.urls"

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

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
        "OPTIONS": {
            "timeout": 20.0,
            "isolation_level": "IMMEDIATE",
            "uri": False,
            "check_same_thread": False,
        },
        "CONN_MAX_AGE": 0,
    }
}


@receiver(connection_created)
def _configure_sqlite_connection(sender, connection, **kwargs) -> None:
    if connection.vendor != "sqlite":
        return

    diagnostics = {
        "journal_mode": None,
        "busy_timeout_ms": None,
        "foreign_keys": None,
        "synchronous": None,
    }

    with connection.cursor() as cursor:
        cursor.execute("PRAGMA journal_mode = WAL;")
        cursor.execute("PRAGMA busy_timeout = 20000;")
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.execute("PRAGMA synchronous = NORMAL;")

        cursor.execute("PRAGMA journal_mode;")
        diagnostics["journal_mode"] = cursor.fetchone()[0] if cursor.description else None
        cursor.execute("PRAGMA busy_timeout;")
        diagnostics["busy_timeout_ms"] = cursor.fetchone()[0] if cursor.description else None
        cursor.execute("PRAGMA foreign_keys;")
        diagnostics["foreign_keys"] = cursor.fetchone()[0] if cursor.description else None
        cursor.execute("PRAGMA synchronous;")
        diagnostics["synchronous"] = cursor.fetchone()[0] if cursor.description else None

    connection._vibe_sqlite_pragma_applied = True
    logger.info(
        "SQLite pragmas configured for database=%s: %s",
        connection.alias,
        diagnostics,
    )


LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "vibe_sqlite": {
            "format": "[{levelname}] {asctime} {name} {message}",
            "style": "{",
        }
    },
    "handlers": {
        "vibe_sqlite_console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "vibe_sqlite",
        }
    },
    "loggers": {
        VIBE_SQLITE_LOGGER: {
            "handlers": ["vibe_sqlite_console"],
            "level": "INFO",
            "propagate": False,
        }
    },
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "ko-kr"
TIME_ZONE = "Asia/Seoul"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = "accounts.User"

AUTHENTICATION_BACKENDS = (
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
)

SITE_ID = 1

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"
LOGOUT_REDIRECT_URL = "/"
LOGOUT_URL = "/logout/"
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["username*", "email*", "password1*", "password2*"]
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_LOGOUT_REDIRECT_URL = "/"

CRISPY_TEMPLATE_PACK = "bootstrap4"
TAILWIND_APP_NAME = "theme"
NPM_BIN_PATH = os.environ.get("NPM_BIN_PATH", "npm")

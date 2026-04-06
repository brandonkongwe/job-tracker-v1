"""
Development settings — extends base.
Sets DEBUG=True, uses console email, enables debug toolbar.
"""

from .base import * 

DEBUG = True

# Allow all hosts in dev
ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar
INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405
INTERNAL_IPS = ["127.0.0.1"]

# Always use console email in dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Relax password validation in dev
AUTH_PASSWORD_VALIDATORS = []

# Logging — print SQL queries to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "loggers": {
        "django.db.backends": {
            "handlers": ["console"],
            "level": "DEBUG",
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
        },
    },
}
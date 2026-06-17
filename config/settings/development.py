import os

from .base import *  # noqa: F401, F403

DEBUG = True

# django-debug-toolbar es solo para desarrollo interactivo: bajo pytest rompe
# cualquier vista que use el test Client (intenta resolver el namespace 'djdt'
# antes de que las urls del toolbar terminen de registrarse en ese contexto).
RUNNING_UNDER_PYTEST = "PYTEST_VERSION" in os.environ

if not RUNNING_UNDER_PYTEST:
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]  # noqa: F405

# Muestra el toolbar en Docker (la IP interna no es 127.0.0.1)
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,
}

# Emails van a consola en desarrollo
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {"class": "logging.StreamHandler"},
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

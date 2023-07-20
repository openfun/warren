"""Django settings for warren project."""

import json
from pathlib import Path
from typing import List

import sentry_sdk
from configurations import Configuration, values
from django.utils.translation import gettext_lazy as _
from sentry_sdk.integrations.django import DjangoIntegration

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


def get_release():
    """Get the current release of the application.

    By release, we mean the release from the version.json file à la Mozilla [1]
    (if any). If this file has not been found, it defaults to "NA".
    [1]
    https://github.com/mozilla-services/Dockerflow/blob/master/docs/version_object.md.
    """
    # Try to get the current release from the version.json file generated by the
    # CI during the Docker image build
    try:
        with (BASE_DIR / Path("version.json")).open(encoding="utf8") as version:
            return json.load(version)["version"]
    except FileNotFoundError:
        return "NA"  # Default: not available


class Base(Configuration):
    """Base configuration every configuration should inherit from.

    This is the base configuration every configuration (aka environnement)
    should inherit from. It is recommended to configure third-party
    applications by creating a configuration mixins in ./configurations and
    compose the Base configuration with those mixins.

    It depends on an environment variable that SHOULD be defined:

    * DJANGO_SECRET_KEY

    You may also want to override default configuration by setting the
    following environment variables:

    * DB_NAME
    * DB_HOST
    * DB_PASSWORD
    * DB_USER
    """

    AUTHENTICATION_BACKENDS = [
        "lti_toolbox.backend.LTIBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]

    DEBUG = False

    # Security
    ALLOWED_HOSTS: List[str] = []
    SECRET_KEY = values.Value(None)

    # SECURE_PROXY_SSL_HEADER allows to fix the scheme in Django's HttpRequest
    # object when you application is behind a reverse proxy.
    #
    # Keep this SECURE_PROXY_SSL_HEADER configuration only if :
    # - your Django app is behind a proxy.
    # - your proxy strips the X-Forwarded-Proto header from all incoming requests
    # - Your proxy sets the X-Forwarded-Proto header and sends it to Django
    #
    # In other cases, you should comment the following line to avoid security issues.
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

    # Disable Samesite flag in session and csrf cookies, because a LTI tool provider app
    # is meant to run in an iframe on external websites.
    # Note : The better solution is to send a flag Samesite=none, because
    # modern browsers are considering Samesite=Lax by default when the flag is
    # not specified.
    # It will be possible to specify CSRF_COOKIE_SAMESITE="none" in Django 3.1
    CSRF_COOKIE_SAMESITE = None
    SESSION_COOKIE_SAMESITE = None

    # Password validation
    # https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

    AUTH_PASSWORD_VALIDATORS = [
        {"NAME": name}
        for name in [
            "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
            "django.contrib.auth.password_validation.MinimumLengthValidator",
            "django.contrib.auth.password_validation.CommonPasswordValidator",
            "django.contrib.auth.password_validation.NumericPasswordValidator",
        ]
    ]

    # Privacy
    SECURE_REFERRER_POLICY = "same-origin"

    # Application definition
    ROOT_URLCONF = "warren.urls"
    WSGI_APPLICATION = "warren.wsgi.application"

    # Internationalization
    # https://docs.djangoproject.com/en/4.1/topics/i18n/
    TIME_ZONE = "Europe/Paris"
    USE_I18N = True
    USE_L10N = True
    USE_TZ = True
    LOCALE_PATHS = [BASE_DIR / Path("locale")]
    LANGUAGE_CODE = "fr"
    LANGUAGES = [
        ("fr", _("French")),
        ("en", _("English")),
    ]

    # Static files (CSS, JavaScript, Images)
    # https://docs.djangoproject.com/en/4.1/howto/static-files/
    STATIC_URL = "static/"
    STATIC_ROOT = values.Value(BASE_DIR / "staticfiles")

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    # Database
    DATABASES = {
        "default": {
            "ENGINE": values.Value(
                "django.db.backends.postgresql_psycopg2",
                environ_name="DB_ENGINE",
                environ_prefix=None,
            ),
            "NAME": values.Value("lti", environ_name="DB_NAME", environ_prefix=None),
            "USER": values.Value("fun", environ_name="DB_USER", environ_prefix=None),
            "PASSWORD": values.Value(
                "pass", environ_name="DB_PASSWORD", environ_prefix=None
            ),
            "HOST": values.Value(
                "localhost", environ_name="DB_HOST", environ_prefix=None
            ),
            "PORT": values.Value(5432, environ_name="DB_PORT", environ_prefix=None),
        }
    }

    # Templates
    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                    "django.template.context_processors.csrf",
                    "django.template.context_processors.debug",
                    "django.template.context_processors.i18n",
                    "django.template.context_processors.media",
                    "django.template.context_processors.request",
                    "django.template.context_processors.tz",
                ],
            },
        },
    ]

    MIDDLEWARE = [
        "django.middleware.security.SecurityMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "dockerflow.django.middleware.DockerflowMiddleware",
    ]

    # Django applications from the highest priority to the lowest
    INSTALLED_APPS = [
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Runtime
        "dockerflow.django",
        # LTI Toolbox
        "lti_toolbox",
        # Utilities
        "apps.development",
        "apps.lti",
        "apps.dashboards",
    ]

    # Cache
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }

    # Sentry
    SENTRY_DSN = values.Value(None, environ_name="SENTRY_DSN")

    # Warren
    # Should be a dict with platform urls as keys and corresponding edx API
    # keys as values.
    EDX_PLATFORM_API_TOKENS = values.DictValue(
        {}, environ_name="EDX_PLATFORM_API_TOKENS", environ_prefix=None
    )

    @classmethod
    def post_setup(cls):
        """Post setup configuration.

        This is the place where you can configure settings that require other
        settings to be loaded.
        """
        super().post_setup()

        # The SENTRY_DSN setting should be available to activate sentry for an env.
        if cls.SENTRY_DSN is not None:
            sentry_sdk.init(
                dsn=cls.SENTRY_DSN,
                environment=cls.__name__.lower(),
                release=get_release(),
                integrations=[DjangoIntegration()],
            )


class Development(Base):
    """Development environment settings.

    We set DEBUG to True and configure the server to respond from all hosts.
    """

    DEBUG = True
    ALLOWED_HOSTS = ["*"]

    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "verbose": {
                "format": "[%(levelname)s] [%(asctime)s] [%(module)s] "
                "%(process)d %(thread)d %(message)s"
            }
        },
        "handlers": {
            "console": {
                "level": "DEBUG",
                "class": "logging.StreamHandler",
                "formatter": "verbose",
            }
        },
        "loggers": {
            "oauthlib": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
            "lti_toolbox": {
                "handlers": ["console"],
                "level": "DEBUG",
                "propagate": True,
            },
            "django": {"handlers": ["console"], "level": "INFO", "propagate": True},
            "apps.lti": {"handlers": ["console"], "level": "DEBUG", "propagate": True},
        },
    }


class Test(Base):
    """Test environment settings."""


class ContinuousIntegration(Test):
    """Continous Integration environment settings.

    nota bene: it should inherit from the Test environment.
    """


class Production(Base):
    """Production environment settings.

    You must define the DJANGO_ALLOWED_HOSTS environment variable in Production
    configuration (and derived configurations):
    DJANGO_ALLOWED_HOSTS="foo.com,foo.fr".
    """

    # Security
    ALLOWED_HOSTS = values.ListValue(None)
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    # System check reference:
    # https://docs.djangoproject.com/en/2.2/ref/checks/#security
    SILENCED_SYSTEM_CHECKS = values.ListValue(
        [
            # Allow to disable django.middleware.clickjacking.XFrameOptionsMiddleware
            # It is necessary since the LTI tool provider application will be displayed
            # in an iframe on external LMS sites.
            "security.W002",
            # SECURE_SSL_REDIRECT is not defined in the base configuration
            "security.W008",
            # No value is defined for SECURE_HSTS_SECONDS
            "security.W004",
        ]
    )


class Feature(Production):
    """Feature environment settings.

    nota bene: it should inherit from the Production environment.
    """


class Staging(Production):
    """Staging environment settings.

    nota bene: it should inherit from the Production environment.
    """


class PreProduction(Production):
    """Pre-production environment settings.

    nota bene: it should inherit from the Production environment.
    """
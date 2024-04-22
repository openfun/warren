"""Django settings for warren project."""

import json
import os
import uuid
from datetime import timedelta
from pathlib import Path
from typing import List

import sentry_sdk
from configurations import Configuration, values
from django.utils.log import DEFAULT_LOGGING
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


DEFAULT_ENVIRON_PREFIX = "WARREN_APP"


class Value(values.Value):
    """Custom Value instance that overrides default Value configuration."""

    def __init__(  # noqa: PLR0913
        self,
        default=None,
        environ=True,
        environ_name=None,
        environ_prefix=DEFAULT_ENVIRON_PREFIX,
        environ_required=False,
        *args,
        **kwargs,
    ):
        """Override the environ_prefix default to avoid repeting it."""
        super().__init__(
            default=default,
            environ=environ,
            environ_name=environ_name,
            environ_prefix=environ_prefix,
            environ_required=environ_required,
            *args,  # noqa: B026
            **kwargs,
        )


class DictValue(Value, values.DictValue):
    """Custom DictValue that inherits from our custom Value class."""


class FloatValue(Value, values.FloatValue):
    """Custom FloatValue that inherits from our custom Value class."""


class ListValue(Value, values.ListValue):
    """Custom ListValue that inherits from our custom Value class."""


class Base(Configuration):
    """Base configuration every configuration should inherit from.

    This is the base configuration every configuration (aka environment)
    should inherit from. It is recommended to configure third-party
    applications by creating a configuration mixins in ./configurations and
    compose the Base configuration with those mixins.

    It depends on an environment variable that SHOULD be defined:

    * WARREN_APP_SECRET_KEY

    You may also want to override default configuration by setting the
    following environment variables:

    * WARREN_APP_DB_NAME
    * WARREN_APP_DB_HOST
    * WARREN_APP_DB_PASSWORD
    * WARREN_APP_DB_USER
    """

    AUTHENTICATION_BACKENDS = [
        "lti_toolbox.backend.LTIBackend",
        "django.contrib.auth.backends.ModelBackend",
    ]

    DEBUG = False

    # Security
    ALLOWED_HOSTS: List[str] = ListValue()
    SECRET_KEY = Value(None)

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
    STATIC_ROOT = Value(BASE_DIR / Path("static"))
    STATIC_URL = "static/"
    STATICFILES_DIRS = [os.path.join(BASE_DIR, "staticfiles")]

    # Media
    MEDIA_ROOT = Value(BASE_DIR / Path("media"))

    # Storages
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "whitenoise.storage.CompressedStaticFilesStorage",
        },
    }

    # Default primary key field type
    # https://docs.djangoproject.com/en/4.1/ref/settings/#default-auto-field
    DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

    # Database
    DATABASES = {
        "default": {
            "ENGINE": Value(
                "django.db.backends.postgresql_psycopg2",
                environ_name="DB_ENGINE",
            ),
            "NAME": Value("warren-app", environ_name="DB_NAME"),
            "USER": Value("fun", environ_name="DB_USER"),
            "PASSWORD": Value("pass", environ_name="DB_PASSWORD"),
            "HOST": Value("localhost", environ_name="DB_HOST"),
            "PORT": Value(5432, environ_name="DB_PORT"),
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
        "whitenoise.middleware.WhiteNoiseMiddleware",
        "django.contrib.sessions.middleware.SessionMiddleware",
        "django.middleware.locale.LocaleMiddleware",
        "corsheaders.middleware.CorsMiddleware",
        "django.middleware.common.CommonMiddleware",
        "django.middleware.csrf.CsrfViewMiddleware",
        "django.contrib.auth.middleware.AuthenticationMiddleware",
        "django.contrib.messages.middleware.MessageMiddleware",
        "dockerflow.django.middleware.DockerflowMiddleware",
    ]

    # Django applications from the highest priority to the lowest
    INSTALLED_APPS = [
        "whitenoise.runserver_nostatic",
        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        # Runtime
        "dockerflow.django",
        # CORS
        "corsheaders",
        # LTI Toolbox
        "lti_toolbox",
        # Utilities
        "rest_framework_simplejwt",
        "apps.token",
        "apps.development",
        "apps.lti",
    ]

    # Cache
    CACHES = {
        "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    }

    # Sentry
    SENTRY_DSN = Value(None)

    # LTI
    LTI_CONFIG_TITLE = Value("Warren")
    LTI_CONFIG_DESCRIPTION = Value(
        "An opensource visualization platform for learning analytics."
    )
    LTI_CONFIG_ICON = Value("warren_52x52.svg")
    LTI_CONFIG_URL = Value()
    LTI_CONFIG_CONTACT_EMAIL = Value()

    REST_FRAMEWORK = {
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "rest_framework_simplejwt.authentication.JWTAuthentication",
        ],
        "DEFAULT_VERSIONING_CLASS": "rest_framework.versioning.URLPathVersioning",
    }

    LTI_ACCESS_TOKEN_LIFETIME = timedelta(
        seconds=FloatValue(default=86400, environ_name="LTI_ACCESS_TOKEN_LIFETIME")
    )

    SIMPLE_JWT = {
        "ACCESS_TOKEN_LIFETIME": timedelta(
            seconds=FloatValue(
                default=300,
                environ_name="ACCESS_TOKEN_LIFETIME",
            )
        ),
        "REFRESH_TOKEN_LIFETIME": timedelta(
            seconds=FloatValue(
                default=86400,
                environ_name="REFRESH_TOKEN_LIFETIME",
            )
        ),
        "ALGORITHM": Value("HS256", environ_name="SIGNING_ALGORITHM"),
        "SIGNING_KEY": Value(None, environ_name="SIGNING_KEY"),
        "AUTH_TOKEN_CLASSES": (
            "rest_framework_simplejwt.tokens.AccessToken",
            "apps.lti.token.LTIAccessToken",
        ),
    }

    CORS_ALLOWED_ORIGINS = ListValue()

    LOGGING = DictValue(DEFAULT_LOGGING)

    # Frontend
    ROOT_URLS = {
        "API_ROOT_URL": Value(
            "", environ_name="WARREN_API_ROOT_URL", environ_prefix=None
        ),
        "APP_ROOT_URL": Value("", environ_name="ROOT_URL"),
    }

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


class Build(Base):
    """Settings used when the application is built.

    This environment should not be used to run the application. Just to build it with
    non blocking settings.
    """

    SECRET_KEY = Value("DummyKey")


class Development(Base):
    """Development environment settings.

    We set DEBUG to True and configure the server to respond from all hosts.
    """

    DEBUG = True
    ALLOWED_HOSTS = ["*"]

    # LTI parameters
    LTI_PARAMETERS = {
        "lti_message_type": "basic-lti-launch-request",
        "lti_version": "LTI-1p0",
        "resource_link_id": str(uuid.uuid4()),
        "lis_person_contact_email_primary": Value(
            "johndoe@example.com", environ_name="LTI_LIS_PERSON_CONTACT_EMAIL_PRIMARY"
        ),
        "user_id": Value("1234", environ_name="LTI_USER_ID"),
        "context_id": Value(
            "course-v1:openfun+mathematics101+session01", environ_name="LTI_CONTEXT_ID"
        ),
        "context_title": Value("Mathematics 101", environ_name="LTI_CONTEXT_TITLE"),
        "roles": Value("teacher", environ_name="LTI_ROLES"),
        "launch_presentation_locale": Value(
            "fr", environ_name="LTI_LAUNCH_PRESENTATION_LOCALE"
        ),
    }

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
    """Continuous Integration environment settings.

    nota bene: it should inherit from the Test environment.
    """


class Production(Base):
    """Production environment settings.

    You must define the WARREN_APP_ALLOWED_HOSTS environment variable in Production
    configuration (and derived configurations):
    WARREN_APP_ALLOWED_HOSTS="foo.com,foo.fr".
    """

    # Security
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    # System check reference:
    # https://docs.djangoproject.com/en/2.2/ref/checks/#security
    SILENCED_SYSTEM_CHECKS = ListValue(
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

"""The development app."""

from django.apps import AppConfig


class DevelopmentConfig(AppConfig):
    """Configuration for the development app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.development"

"""Shell application configuration."""

from django.apps import AppConfig


class ShellConfig(AppConfig):
    """Configure the thin shell presentation application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "libraryops.shell"

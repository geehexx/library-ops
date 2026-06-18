"""Circulation application configuration."""

from django.apps import AppConfig


class CirculationConfig(AppConfig):
    """Configure the circulation application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "libraryops.circulation"

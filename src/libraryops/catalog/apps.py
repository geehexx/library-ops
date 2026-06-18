"""Catalog application configuration."""

from django.apps import AppConfig


class CatalogConfig(AppConfig):
    """Configure the catalog application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "libraryops.catalog"

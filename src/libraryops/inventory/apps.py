"""Inventory application configuration."""

from django.apps import AppConfig


class InventoryConfig(AppConfig):
    """Configure the inventory application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "libraryops.inventory"

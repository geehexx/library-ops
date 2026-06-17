"""Audit application configuration."""

from django.apps import AppConfig


class AuditConfig(AppConfig):
    """Configure the audit application."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "libraryops.audit"

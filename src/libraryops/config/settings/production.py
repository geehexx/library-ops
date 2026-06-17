# pyright: reportConstantRedefinition=false
"""Production Django settings."""

from __future__ import annotations

import os
from typing import Any, cast

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .base import *  # noqa: F403

DEBUG = False


def require_env(name: str) -> str:
    """Return a required environment variable or fail loudly."""
    value = os.getenv(name)
    if value is None or not value.strip():
        raise ImproperlyConfigured(f"Production settings require {name}.")
    return value


def parse_required_csv_env(name: str) -> list[str]:
    """Return a required comma-separated environment variable."""
    values = [value.strip() for value in require_env(name).split(",") if value.strip()]
    if not values:
        raise ImproperlyConfigured(f"Production settings require at least one value for {name}.")
    return values


def build_required_database() -> dict[str, Any]:
    """Build the production database configuration from a required URL."""
    database_url = require_env("DATABASE_URL")
    return cast("dict[str, Any]", dj_database_url.parse(database_url))


SECRET_KEY = require_env("SECRET_KEY")
ALLOWED_HOSTS = parse_required_csv_env("DJANGO_ALLOWED_HOSTS")
DATABASES = {"default": build_required_database()}

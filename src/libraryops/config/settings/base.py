"""Base Django settings for Library Ops."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, cast

import dj_database_url
from django.core.management.utils import get_random_secret_key

BASE_DIR = Path(__file__).resolve().parents[4]
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY") or get_random_secret_key()
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"


def parse_csv_env(name: str, default: str) -> list[str]:
    """Split a comma-separated environment variable into cleaned items.

    Args:
        name: Environment variable name to read.
        default: Default comma-separated fallback value.

    Returns:
        A list of non-empty trimmed values.
    """
    return [value.strip() for value in os.getenv(name, default).split(",") if value.strip()]


def build_default_database() -> dict[str, Any]:
    """Build the default Django database configuration.

    Returns:
        A database configuration dictionary using `DATABASE_URL` when present,
        otherwise the local SQLite fallback.
    """
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return cast("dict[str, Any]", dj_database_url.parse(database_url))
    return {
        "ENGINE": os.getenv("DJANGO_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.getenv("DJANGO_DB_NAME", str(BASE_DIR / "db.sqlite3")),
    }


ALLOWED_HOSTS = parse_csv_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "libraryops.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "libraryops.config.wsgi.application"
ASGI_APPLICATION = "libraryops.config.asgi.application"

DATABASES = {"default": build_default_database()}

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

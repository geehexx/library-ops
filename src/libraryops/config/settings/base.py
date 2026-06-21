"""Base Django settings for Library Ops."""

from __future__ import annotations

import os
import tempfile
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


def build_socialaccount_configuration() -> tuple[list[str], dict[str, Any]]:
    """Build optional allauth socialaccount apps and provider settings.

    Returns:
        A tuple of installed app labels and provider settings for enabled
        OAuth providers. When no provider credentials exist, both entries are
        empty so local email/password auth stays the default.
    """

    provider_defs = [
        (
            "google",
            "allauth.socialaccount.providers.google",
            "DJANGO_ALLAUTH_GOOGLE_CLIENT_ID",
            "DJANGO_ALLAUTH_GOOGLE_SECRET",
            {
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"access_type": "online"},
                "OAUTH_PKCE_ENABLED": True,
            },
        ),
        (
            "github",
            "allauth.socialaccount.providers.github",
            "DJANGO_ALLAUTH_GITHUB_CLIENT_ID",
            "DJANGO_ALLAUTH_GITHUB_SECRET",
            {
                "SCOPE": ["user"],
                "VERIFIED_EMAIL": True,
            },
        ),
    ]
    installed_apps: list[str] = []
    provider_settings: dict[str, Any] = {}
    for provider_name, app_label, client_id_env, secret_env, defaults in provider_defs:
        client_id = os.getenv(client_id_env, "").strip()
        secret = os.getenv(secret_env, "").strip()
        if not client_id or not secret:
            continue
        if "allauth.socialaccount" not in installed_apps:
            installed_apps.append("allauth.socialaccount")
        installed_apps.append(app_label)
        provider_settings[provider_name] = {
            "APPS": [
                {
                    "client_id": client_id,
                    "secret": secret,
                    "key": "",
                }
            ]
        }
        provider_settings[provider_name].update(defaults)
    return installed_apps, provider_settings


ALLOWED_HOSTS = parse_csv_env("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver")

SOCIALACCOUNT_INSTALLED_APPS, SOCIALACCOUNT_PROVIDERS = build_socialaccount_configuration()

INSTALLED_APPS = [
    "unfold",
    "unfold.contrib.guardian",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "libraryops.accounts",  # This must be before allauth to ensure our templates over-ride.
    "allauth",
    "allauth.account",
    "guardian",
    "libraryops.catalog",
    "libraryops.inventory",
    "libraryops.circulation",
    "libraryops.audit",
    "libraryops.shell",
]
INSTALLED_APPS.extend(SOCIALACCOUNT_INSTALLED_APPS)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django_htmx.middleware.HtmxMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "libraryops.config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": cast("list[Path]", []),
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
MEDIA_URL = "/media/"
MEDIA_ROOT = Path(
    os.getenv("DJANGO_MEDIA_ROOT", str(Path(tempfile.gettempdir()) / "libraryops-media"))
)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
SITE_ID = 1
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
ANONYMOUS_USER_NAME = None
ACCOUNT_EMAIL_VERIFICATION = "none"
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]
# This demo does not expose a social-account connect flow, so skipping the
# allauth confirmation interstitial keeps hosted login UX intentional.
SOCIALACCOUNT_LOGIN_ON_GET = True

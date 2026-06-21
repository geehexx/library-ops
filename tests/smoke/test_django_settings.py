"""Settings-focused tests for Django bootstrap hardening."""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest


def reload_module(module_name: str):
    """Import a settings module after environment-variable changes.

    Args:
        module_name: Fully qualified module name to reload.

    Returns:
        The reloaded Python module object.
    """

    sys.modules.pop(module_name, None)
    if (
        module_name.startswith("libraryops.config.settings.")
        and module_name != "libraryops.config.settings.base"
    ):
        sys.modules.pop("libraryops.config.settings.base", None)
    return importlib.import_module(module_name)


def test_base_settings_default_to_sqlite(monkeypatch: Any) -> None:
    """Ensure base settings fall back to SQLite and include the test host.

    Args:
        monkeypatch: Pytest environment patch helper.
    """

    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DJANGO_DB_ENGINE", raising=False)
    monkeypatch.delenv("DJANGO_DB_NAME", raising=False)
    monkeypatch.delenv("DJANGO_ALLOWED_HOSTS", raising=False)

    settings_module = reload_module("libraryops.config.settings.base")

    assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert settings_module.DATABASES["default"]["NAME"] == str(
        settings_module.BASE_DIR / "db.sqlite3"
    )
    assert "testserver" in settings_module.ALLOWED_HOSTS


def test_base_settings_use_database_url_when_present(
    monkeypatch: Any,
) -> None:
    """Ensure `DATABASE_URL` selects Postgres settings.

    Args:
        monkeypatch: Pytest environment patch helper.
    """

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://libraryops:libraryops@localhost:5432/libraryops_test",
    )

    settings_module = reload_module("libraryops.config.settings.base")

    assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert settings_module.DATABASES["default"]["NAME"] == "libraryops_test"
    assert settings_module.DATABASES["default"]["USER"] == "libraryops"
    assert settings_module.DATABASES["default"]["HOST"] == "localhost"
    assert settings_module.DATABASES["default"]["PORT"] == 5432


def test_base_settings_disable_socialaccount_by_default(monkeypatch: Any) -> None:
    """Ensure optional OAuth providers stay disabled without credentials."""

    monkeypatch.delenv("DJANGO_ALLAUTH_GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("DJANGO_ALLAUTH_GOOGLE_SECRET", raising=False)
    monkeypatch.delenv("DJANGO_ALLAUTH_GITHUB_CLIENT_ID", raising=False)
    monkeypatch.delenv("DJANGO_ALLAUTH_GITHUB_SECRET", raising=False)

    settings_module = reload_module("libraryops.config.settings.base")

    assert "allauth.socialaccount" not in settings_module.INSTALLED_APPS
    assert "allauth.socialaccount.providers.google" not in settings_module.INSTALLED_APPS
    assert "allauth.socialaccount.providers.github" not in settings_module.INSTALLED_APPS
    assert settings_module.SOCIALACCOUNT_PROVIDERS == {}
    assert settings_module.SOCIALACCOUNT_LOGIN_ON_GET is True


@pytest.mark.parametrize(
    ("provider", "client_id_env", "secret_env", "provider_app", "provider_defaults"),
    [
        (
            "google",
            "DJANGO_ALLAUTH_GOOGLE_CLIENT_ID",
            "DJANGO_ALLAUTH_GOOGLE_SECRET",
            "allauth.socialaccount.providers.google",
            {
                "SCOPE": ["profile", "email"],
                "AUTH_PARAMS": {"access_type": "online"},
                "OAUTH_PKCE_ENABLED": True,
            },
        ),
        (
            "github",
            "DJANGO_ALLAUTH_GITHUB_CLIENT_ID",
            "DJANGO_ALLAUTH_GITHUB_SECRET",
            "allauth.socialaccount.providers.github",
            {
                "SCOPE": ["user"],
                "VERIFIED_EMAIL": True,
            },
        ),
    ],
)
def test_base_settings_enable_socialaccount_provider_from_env(
    monkeypatch: Any,
    provider: str,
    client_id_env: str,
    secret_env: str,
    provider_app: str,
    provider_defaults: dict[str, Any],
) -> None:
    """Ensure each OAuth provider appears only when its env vars are set."""

    for env_name in (
        "DJANGO_ALLAUTH_GOOGLE_CLIENT_ID",
        "DJANGO_ALLAUTH_GOOGLE_SECRET",
        "DJANGO_ALLAUTH_GITHUB_CLIENT_ID",
        "DJANGO_ALLAUTH_GITHUB_SECRET",
    ):
        monkeypatch.delenv(env_name, raising=False)

    monkeypatch.setenv(client_id_env, f"{provider}-client-id")
    monkeypatch.setenv(secret_env, f"{provider}-secret")

    settings_module = reload_module("libraryops.config.settings.base")

    assert "allauth.socialaccount" in settings_module.INSTALLED_APPS
    assert provider_app in settings_module.INSTALLED_APPS
    assert set(settings_module.SOCIALACCOUNT_PROVIDERS) == {provider}
    assert settings_module.SOCIALACCOUNT_LOGIN_ON_GET is True
    assert settings_module.SOCIALACCOUNT_PROVIDERS[provider] == {
        "APPS": [
            {
                "client_id": f"{provider}-client-id",
                "secret": f"{provider}-secret",
                "key": "",
            }
        ],
        **provider_defaults,
    }
    other_provider_app = (
        "allauth.socialaccount.providers.github"
        if provider == "google"
        else "allauth.socialaccount.providers.google"
    )
    assert other_provider_app not in settings_module.INSTALLED_APPS


def test_test_settings_only_override_sqlite_without_database_url(
    monkeypatch: Any,
) -> None:
    """Ensure test settings force in-memory SQLite only without `DATABASE_URL`.

    Args:
        monkeypatch: Pytest environment patch helper.
    """

    monkeypatch.delenv("DATABASE_URL", raising=False)

    settings_module = reload_module("libraryops.config.settings.test")

    assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3"
    assert settings_module.DATABASES["default"]["NAME"] == ":memory:"


def test_test_settings_respect_database_url(monkeypatch: Any) -> None:
    """Ensure test settings preserve Postgres when `DATABASE_URL` is set.

    Args:
        monkeypatch: Pytest environment patch helper.
    """

    monkeypatch.setenv(
        "DATABASE_URL",
        "postgres://libraryops:libraryops@localhost:5432/libraryops_test",
    )

    settings_module = reload_module("libraryops.config.settings.test")

    assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert settings_module.DATABASES["default"]["NAME"] == "libraryops_test"

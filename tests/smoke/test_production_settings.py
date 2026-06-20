"""Smoke tests for production Django settings."""

from __future__ import annotations

import importlib
import sys
from typing import Any

import pytest
from django.core.exceptions import ImproperlyConfigured


def reload_module(module_name: str) -> Any:
    """Import a settings module from a clean state."""
    sys.modules.pop(module_name, None)
    return importlib.import_module(module_name)


@pytest.mark.parametrize(
    ("missing_env", "expected_message"),
    [
        ("SECRET_KEY", "Production settings require SECRET_KEY."),
        ("DATABASE_URL", "Production settings require DATABASE_URL."),
        ("DJANGO_ALLOWED_HOSTS", "Production settings require DJANGO_ALLOWED_HOSTS."),
    ],
)
def test_production_settings_fail_loudly_when_required_env_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    missing_env: str,
    expected_message: str,
) -> None:
    """Ensure the production module raises when a required env var is absent."""
    monkeypatch.delenv("SECRET_KEY", raising=False)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("DJANGO_ALLOWED_HOSTS", raising=False)

    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")
    monkeypatch.setenv(
        "DATABASE_URL", "postgres://libraryops:libraryops@localhost:5432/libraryops_prod"
    )
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "libraryops.example.com")
    monkeypatch.delenv(missing_env, raising=False)

    with pytest.raises(ImproperlyConfigured, match=expected_message):
        reload_module("libraryops.config.settings.production")


@pytest.mark.parametrize(
    ("blank_env", "blank_value", "expected_message"),
    [
        ("SECRET_KEY", "   ", "Production settings require SECRET_KEY."),
        (
            "DJANGO_ALLOWED_HOSTS",
            "  ,  ",
            "Production settings require at least one value for DJANGO_ALLOWED_HOSTS.",
        ),
    ],
)
def test_production_settings_reject_blank_and_whitespace_env_values(
    monkeypatch: pytest.MonkeyPatch,
    blank_env: str,
    blank_value: str,
    expected_message: str,
) -> None:
    """Ensure production settings reject blank and whitespace-only values."""
    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")
    monkeypatch.setenv(
        "DATABASE_URL", "postgres://libraryops:libraryops@localhost:5432/libraryops_prod"
    )
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "libraryops.example.com")
    monkeypatch.setenv(blank_env, blank_value)

    with pytest.raises(ImproperlyConfigured, match=expected_message):
        reload_module("libraryops.config.settings.production")


def test_production_settings_use_explicit_secure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ensure production settings load only from explicit secure environment values."""
    monkeypatch.setenv("SECRET_KEY", "prod-secret-key")
    monkeypatch.setenv(
        "DATABASE_URL", "postgres://libraryops:libraryops@localhost:5432/libraryops_prod"
    )
    monkeypatch.setenv(
        "DJANGO_ALLOWED_HOSTS",
        " libraryops.example.com , , api.libraryops.example.com ",
    )

    settings_module = reload_module("libraryops.config.settings.production")

    assert settings_module.DEBUG is False
    assert settings_module.SECRET_KEY == "prod-secret-key"
    assert settings_module.ALLOWED_HOSTS == [
        "libraryops.example.com",
        "api.libraryops.example.com",
    ]
    assert settings_module.MIDDLEWARE[0] == "whitenoise.middleware.WhiteNoiseMiddleware"
    assert settings_module.STORAGES["staticfiles"]["BACKEND"] == (
        "whitenoise.storage.CompressedManifestStaticFilesStorage"
    )
    assert settings_module.DATABASES["default"]["ENGINE"] == "django.db.backends.postgresql"
    assert settings_module.DATABASES["default"]["NAME"] == "libraryops_prod"

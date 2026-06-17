"""Settings-focused tests for Django bootstrap hardening."""

from __future__ import annotations

import importlib
import sys
from typing import Any


def reload_module(module_name: str):
    """Import a settings module after environment-variable changes.

    Args:
        module_name: Fully qualified module name to reload.

    Returns:
        The reloaded Python module object.
    """

    sys.modules.pop(module_name, None)
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

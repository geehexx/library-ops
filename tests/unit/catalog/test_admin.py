"""Tests for Django admin registrations and operational metadata."""

from __future__ import annotations

from collections.abc import Iterable  # noqa: TC003
from pathlib import Path
from typing import Any, cast

import pytest
from django.contrib import admin

from libraryops.catalog.admin import (
    BibliographicWorkAdmin,
    BookEditionAdmin,
    ContributorAdmin,
    ExternalSourceRecordAdmin,
    WorkContributorAdmin,
)
from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ExternalSourceRecord,
    WorkContributor,
)
from libraryops.inventory.admin import BookCopyAdmin
from libraryops.inventory.models import BookCopy

REPO_ROOT = Path(__file__).resolve().parents[3]
ADMIN_CONTRACTS: tuple[tuple[Any, Any, dict[str, object]], ...] = (
    (
        BibliographicWork,
        BibliographicWorkAdmin,
        {
            "list_display": {
                "title",
                "normalized_title",
                "archived_at",
                "created_at",
                "updated_at",
            },
            "list_filter": {"archived_at"},
            "search_fields": {"title", "normalized_title", "description"},
            "readonly_fields": {"normalized_title", "created_at", "updated_at"},
            "date_hierarchy": "created_at",
        },
    ),
    (
        Contributor,
        ContributorAdmin,
        {
            "list_display": {"name", "normalized_name", "created_at"},
            "search_fields": {"name", "normalized_name"},
            "readonly_fields": {"normalized_name", "created_at"},
            "date_hierarchy": "created_at",
        },
    ),
    (
        WorkContributor,
        WorkContributorAdmin,
        {
            "list_display": {"work", "contributor", "role", "sort_order"},
            "list_filter": {"role"},
            "search_fields": {"work__title", "contributor__name"},
            "autocomplete_fields": {"work", "contributor"},
            "ordering": ("sort_order", "id"),
        },
    ),
    (
        BookEdition,
        BookEditionAdmin,
        {
            "list_display": {
                "work",
                "publisher",
                "publication_year",
                "language",
                "isbn",
                "archived_at",
                "created_at",
            },
            "list_filter": {"language", "archived_at"},
            "search_fields": {"work__title", "publisher", "isbn", "description"},
            "autocomplete_fields": {"work"},
            "readonly_fields": {"created_at", "updated_at"},
            "date_hierarchy": "created_at",
            "list_select_related": {"work"},
        },
    ),
    (
        ExternalSourceRecord,
        ExternalSourceRecordAdmin,
        {
            "list_display": {
                "source_name",
                "source_identifier",
                "work",
                "edition",
                "imported_at",
                "fetched_at",
            },
            "list_filter": {"source_name"},
            "search_fields": {
                "source_name",
                "source_identifier",
                "source_url",
                "license_note",
                "work__title",
                "edition__isbn",
            },
            "autocomplete_fields": {"work", "edition"},
            "readonly_fields": {"imported_at", "fetched_at"},
            "date_hierarchy": "imported_at",
            "list_select_related": {"work", "edition"},
        },
    ),
    (
        BookCopy,
        BookCopyAdmin,
        {
            "list_display": {
                "barcode",
                "edition",
                "status",
                "shelf_location",
                "archived_at",
                "created_at",
            },
            "list_filter": {"status", "archived_at"},
            "search_fields": {
                "barcode",
                "shelf_location",
                "condition_note",
                "edition__isbn",
                "edition__work__title",
            },
            "autocomplete_fields": {"edition"},
            "readonly_fields": {"created_at", "updated_at"},
            "date_hierarchy": "created_at",
            "list_select_related": {"edition"},
        },
    ),
)


def assert_contains_fields(
    actual_fields: Iterable[str],
    expected_fields: Iterable[str],
    label: str,
) -> None:
    """Ensure the admin contract includes every required field."""

    actual = set(actual_fields)
    expected = set(expected_fields)
    missing = expected - actual
    assert not missing, f"{label} is missing required fields: {sorted(missing)}"


def test_admin_modules_keep_runtime_safe_modeladmin_bases() -> None:
    """Prevent generic ModelAdmin subscription from reappearing in source code."""

    for relative_path in (
        "src/libraryops/catalog/admin.py",
        "src/libraryops/inventory/admin.py",
    ):
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8")
        assert "ModelAdmin[" not in text, f"{relative_path} must use runtime-safe bases"


@pytest.mark.parametrize(
    ("model", "admin_class", "contract"),
    ADMIN_CONTRACTS,
    ids=(
        "bibliographic-work",
        "contributor",
        "work-contributor",
        "book-edition",
        "external-source-record",
        "book-copy",
    ),
)
def test_admin_site_registers_expected_models_with_operational_metadata(
    model: Any,
    admin_class: Any,
    contract: dict[str, object],
) -> None:
    """Ensure each expected model is registered with the right admin contract."""

    registry = cast("dict[Any, Any]", admin.site._registry)  # pyright: ignore[reportUnknownMemberType]
    registered_admin = registry.get(model)
    assert registered_admin is not None, f"{model.__name__} is not registered on admin.site"
    assert isinstance(registered_admin, admin_class)

    for attribute_name, expected_value in contract.items():
        actual_value = getattr(registered_admin, attribute_name)
        if attribute_name == "date_hierarchy":
            assert actual_value == expected_value
            continue
        if attribute_name == "ordering":
            assert tuple(actual_value) == tuple(expected_value)  # type: ignore[arg-type]
            continue
        assert_contains_fields(
            actual_value,
            expected_value,  # type: ignore[arg-type]
            f"{admin_class.__name__}.{attribute_name}",
        )

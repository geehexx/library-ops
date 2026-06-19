"""Catalog forms package with behavior-split re-exports."""

from __future__ import annotations

from libraryops.catalog.forms.copy import CopyForm
from libraryops.catalog.forms.edition import EditionForm
from libraryops.catalog.forms.foundation import CatalogFoundationCreateForm
from libraryops.catalog.forms.work import WorkForm

__all__ = [
    "CatalogFoundationCreateForm",
    "CopyForm",
    "EditionForm",
    "WorkForm",
]

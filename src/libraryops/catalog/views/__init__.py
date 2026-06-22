"""Catalog views package with behavior-split re-exports."""

from __future__ import annotations

from libraryops.catalog.views.base import CatalogCreateView, CatalogDetailView, CatalogIndexView
from libraryops.catalog.views.copy import CopyArchiveView, CopyCreateView, CopyUpdateView
from libraryops.catalog.views.edition import (
    EditionArchiveView,
    EditionCreateView,
    EditionUpdateView,
)
from libraryops.catalog.views.work import WorkArchiveView, WorkCreateView, WorkUpdateView

__all__ = [
    "CatalogCreateView",
    "CatalogDetailView",
    "CatalogIndexView",
    "CopyArchiveView",
    "CopyCreateView",
    "CopyUpdateView",
    "EditionArchiveView",
    "EditionCreateView",
    "EditionUpdateView",
    "WorkArchiveView",
    "WorkCreateView",
    "WorkUpdateView",
]

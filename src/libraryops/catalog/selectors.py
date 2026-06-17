"""Read selectors for the catalog foundation slice."""

from __future__ import annotations

from typing import Any

from libraryops.catalog.models import BibliographicWork


def work_list() -> Any:
    """Return the read-optimized foundation work queryset."""

    return BibliographicWork.objects.foundation_index()


def work_detail(work_id: int) -> BibliographicWork:
    """Return one work with related editions and copies."""

    return work_list().get(pk=work_id)

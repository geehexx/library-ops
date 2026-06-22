"""Search application package for Library Ops."""

from __future__ import annotations

from typing import TYPE_CHECKING

from libraryops.catalog.models import BibliographicWork

from .lexical.criteria import CatalogSearchCriteria
from .lexical.engine import CatalogSearchEngine

if TYPE_CHECKING:
    from django.db.models import QuerySet

__all__ = ["search_catalog"]

_SEARCH_ENGINE = CatalogSearchEngine()


def search_catalog(
    query: str | None,
    *,
    queryset: QuerySet[BibliographicWork] | None = None,
    availability: str | None = None,
    contributor: str | None = None,
    subject: str | None = None,
    language: str | None = None,
    source: str | None = None,
) -> QuerySet[BibliographicWork]:
    """Return ranked catalog works for one lexical search string."""

    base_queryset = (
        queryset if queryset is not None else BibliographicWork.objects.foundation_index()
    )
    criteria = CatalogSearchCriteria.from_values(
        query,
        availability=availability,
        contributor=contributor,
        subject=subject,
        language=language,
        source=source,
    )
    return _SEARCH_ENGINE.search(base_queryset, criteria)

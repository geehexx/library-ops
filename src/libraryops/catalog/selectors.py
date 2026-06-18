"""Read selectors for catalog resources."""

from __future__ import annotations

from django.db.models import QuerySet  # noqa: TC002
from django.http import Http404

from libraryops.catalog.models import BibliographicWork, BookEdition
from libraryops.inventory.models import BookCopy


def work_list() -> QuerySet[BibliographicWork]:
    """Return the read-optimized active work queryset."""

    return BibliographicWork.objects.foundation_index()


def work_detail(work_id: int) -> BibliographicWork:
    """Return one active work with related editions and copies."""

    try:
        return work_list().get(pk=work_id)
    except BibliographicWork.DoesNotExist as exc:
        raise Http404("Work not found.") from exc


def edition_list() -> QuerySet[BookEdition]:
    """Return the active edition queryset for API reads."""

    return (
        BookEdition.objects.select_related("work")
        .prefetch_related("copies")
        .filter(archived_at__isnull=True)
    )


def edition_detail(edition_id: int) -> BookEdition:
    """Return one active edition."""

    try:
        return edition_list().get(pk=edition_id)
    except BookEdition.DoesNotExist as exc:
        raise Http404("Edition not found.") from exc


def copy_list() -> QuerySet[BookCopy]:
    """Return the active copy queryset for API reads."""

    return BookCopy.objects.select_related("edition", "edition__work").filter(
        archived_at__isnull=True
    )


def copy_detail(copy_id: int) -> BookCopy:
    """Return one active copy."""

    try:
        return copy_list().get(pk=copy_id)
    except BookCopy.DoesNotExist as exc:
        raise Http404("Copy not found.") from exc

"""Read selectors for catalog resources."""

from __future__ import annotations

from collections.abc import Iterable
from typing import cast

from django.db.models import Q, QuerySet
from django.http import Http404

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    ExternalSourceRecord,
    WorkContributor,
)
from libraryops.inventory.models import BookCopy
from libraryops.search import search_catalog


def work_list(
    query: str | None = None,
    *,
    availability: str | None = None,
    contributor: str | None = None,
    subject: str | None = None,
    language: str | None = None,
    source: str | None = None,
) -> QuerySet[BibliographicWork]:
    """Return the read-optimized active work queryset."""

    return search_catalog(
        query,
        queryset=BibliographicWork.objects.foundation_index(),
        availability=availability,
        contributor=contributor,
        subject=subject,
        language=language,
        source=source,
    )


def work_facet_options(query: str | None = None) -> dict[str, list[str]]:
    """Return live facet option values for the catalog index form."""

    queryset = work_list(query=query)
    work_ids = queryset.values_list("pk", flat=True)
    contributors = list(
        WorkContributor.objects.filter(work_id__in=work_ids)
        .select_related("contributor")
        .order_by("contributor__name")
        .values_list("contributor__name", flat=True)
        .distinct()
    )
    languages = list(
        BookEdition.objects.filter(work_id__in=work_ids, archived_at__isnull=True)
        .order_by("language")
        .values_list("language", flat=True)
        .distinct()
    )
    sources = list(
        ExternalSourceRecord.objects.filter(
            Q(work_id__in=work_ids) | Q(edition__work_id__in=work_ids)
        )
        .order_by("source_name")
        .values_list("source_name", flat=True)
        .distinct()
    )
    subjects = _collect_subject_values(queryset)
    return {
        "availability": _availability_options(queryset),
        "contributors": contributors,
        "subjects": subjects,
        "languages": languages,
        "sources": sources,
    }


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


def _availability_options(_queryset: QuerySet[BibliographicWork]) -> list[str]:
    """Return the live availability states present in one queryset."""

    # Keep the UI minimal: surface the two stable states regardless of the
    # current result set so the server-rendered form stays predictable.
    return ["available", "unavailable"]


def _collect_subject_values(queryset: QuerySet[BibliographicWork]) -> list[str]:
    """Collect unique subject labels from edition provenance metadata."""

    subjects: set[str] = set()
    for identifiers in BookEdition.objects.filter(
        work_id__in=queryset.values_list("pk", flat=True),
        archived_at__isnull=True,
    ).values_list("external_identifiers", flat=True):
        if not isinstance(identifiers, dict):
            continue
        identifiers_dict = cast("dict[str, object]", identifiers)
        raw_subjects: object = identifiers_dict.get("subjects", ())
        if isinstance(raw_subjects, str):
            raw_subjects = (raw_subjects,)
        if not isinstance(raw_subjects, Iterable):
            continue
        for subject in cast("Iterable[object]", raw_subjects):
            if isinstance(subject, str) and subject.strip():
                subjects.add(subject.strip())
    return sorted(subjects, key=str.casefold)

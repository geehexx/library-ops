"""Composable filters over live catalog, provenance, and inventory state."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from django.db.models import Exists, OuterRef, Q, QuerySet

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    ExternalSourceRecord,
    WorkContributor,
    normalize_name,
)
from libraryops.inventory.models import BookCopy, BookCopyStatus

from .criteria import Availability

if TYPE_CHECKING:
    from .criteria import CatalogFacets


@dataclass(frozen=True, slots=True)
class CatalogFacetFilter:
    """Apply selected facets with correlated ``EXISTS`` subqueries.

    ``EXISTS`` preserves one outer row per bibliographic work and lets the
    database stop scanning a related table after the first qualifying row.
    Availability is derived from active edition and copy state; it is never a
    presentation-only flag.
    """

    def apply(
        self,
        queryset: QuerySet[BibliographicWork],
        facets: CatalogFacets,
        *,
        database_vendor: str,
    ) -> QuerySet[BibliographicWork]:
        """Apply every selected facet to a work queryset.

        Args:
            queryset: Active works to restrict.
            facets: Normalized facet values.
            database_vendor: Django database vendor used to select a supported
                JSON lookup.

        Returns:
            The lazily filtered work queryset.
        """

        if facets.contributor is not None:
            queryset = self._by_contributor(queryset, facets.contributor)
        if facets.subject is not None:
            queryset = self._by_subject(
                queryset,
                facets.subject,
                database_vendor=database_vendor,
            )
        if facets.language is not None:
            queryset = self._by_language(queryset, facets.language)
        if facets.source is not None:
            queryset = self._by_source(queryset, facets.source)
        if facets.availability is not None:
            queryset = self._by_availability(queryset, facets.availability)
        return queryset

    @staticmethod
    def _by_contributor(
        queryset: QuerySet[BibliographicWork],
        contributor: str,
    ) -> QuerySet[BibliographicWork]:
        """Filter by exact normalized contributor name.

        Args:
            queryset: Work queryset to restrict.
            contributor: Contributor display name.

        Returns:
            Works linked to the selected contributor.
        """

        relations = WorkContributor.objects.filter(
            work_id=OuterRef("pk"),
            contributor__normalized_name=normalize_name(contributor),
        ).order_by()
        return queryset.filter(Exists(relations))

    @staticmethod
    def _by_subject(
        queryset: QuerySet[BibliographicWork],
        subject: str,
        *,
        database_vendor: str,
    ) -> QuerySet[BibliographicWork]:
        """Filter by an active edition subject stored in JSON metadata.

        PostgreSQL uses JSON-array containment for exact facet semantics.
        SQLite uses a case-insensitive key-transform lookup because its backend
        does not implement JSON ``contains``.

        Args:
            queryset: Work queryset to restrict.
            subject: Subject label.
            database_vendor: Django database vendor.

        Returns:
            Works with at least one matching active edition.
        """

        editions = BookEdition.objects.filter(
            work_id=OuterRef("pk"),
            archived_at__isnull=True,
        ).order_by()
        if database_vendor == "postgresql":
            editions = editions.filter(external_identifiers__subjects__contains=[subject])
        else:
            editions = editions.filter(external_identifiers__subjects__icontains=subject)
        return queryset.filter(Exists(editions))

    @staticmethod
    def _by_language(
        queryset: QuerySet[BibliographicWork],
        language: str,
    ) -> QuerySet[BibliographicWork]:
        """Filter by case-insensitive active-edition language code.

        Args:
            queryset: Work queryset to restrict.
            language: Language code.

        Returns:
            Works with a matching active edition.
        """

        editions = BookEdition.objects.filter(
            work_id=OuterRef("pk"),
            archived_at__isnull=True,
            language__iexact=language,
        ).order_by()
        return queryset.filter(Exists(editions))

    @staticmethod
    def _by_source(
        queryset: QuerySet[BibliographicWork],
        source: str,
    ) -> QuerySet[BibliographicWork]:
        """Filter by work- or active-edition provenance source.

        Args:
            queryset: Work queryset to restrict.
            source: Provenance source name.

        Returns:
            Works backed by a matching source record.
        """

        work_records = ExternalSourceRecord.objects.filter(
            work_id=OuterRef("pk"),
            source_name__iexact=source,
        ).order_by()
        edition_records = ExternalSourceRecord.objects.filter(
            edition__work_id=OuterRef("pk"),
            edition__archived_at__isnull=True,
            source_name__iexact=source,
        ).order_by()
        return queryset.filter(Q(Exists(work_records)) | Q(Exists(edition_records)))

    @staticmethod
    def _by_availability(
        queryset: QuerySet[BibliographicWork],
        availability: Availability,
    ) -> QuerySet[BibliographicWork]:
        """Filter by authoritative active-copy state.

        ``unavailable`` means at least one active inventory copy exists but no
        active copy is currently marked available. Works without inventory are
        not silently classified as unavailable.

        Args:
            queryset: Work queryset to restrict.
            availability: Parsed availability facet.

        Returns:
            Available works, or works with inventory but no available copy.
        """

        active_copies = (
            BookCopy.objects.filter(
                edition__work_id=OuterRef("pk"),
                edition__archived_at__isnull=True,
                archived_at__isnull=True,
            )
            .exclude(status=BookCopyStatus.ARCHIVED)
            .order_by()
        )
        available_copies = active_copies.filter(status=BookCopyStatus.AVAILABLE)
        if availability is Availability.AVAILABLE:
            return queryset.filter(Exists(available_copies))
        return queryset.filter(Exists(active_copies), ~Exists(available_copies))

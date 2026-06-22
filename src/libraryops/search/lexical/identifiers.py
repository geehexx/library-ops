"""Exact identifier match expressions for catalog search.

Every reverse relation is checked with a correlated ``EXISTS`` expression.
That keeps the outer work queryset at one row per work and avoids relying on
``distinct()`` to repair join multiplication after the fact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from django.db.models import BooleanField, Case, Exists, OuterRef, Q, Value, When

from libraryops.catalog.models import BookEdition, ExternalSourceRecord
from libraryops.inventory.models import BookCopy, BookCopyStatus

if TYPE_CHECKING:
    from django.db.models.expressions import Combinable

    from .criteria import SearchTerm

_EXTERNAL_IDENTIFIER_KEYS: Final[tuple[str, ...]] = (
    "openlibrary_work_id",
    "openlibrary_edition_id",
    "openlibrary_id",
    "gutenberg_ebook_id",
    "gutenberg_id",
)


def false_expression() -> Combinable:
    """Return a database-portable boolean false expression."""

    return Value(False, output_field=BooleanField())


@dataclass(frozen=True, slots=True)
class IdentifierMatchBuilder:
    """Build exact ISBN, barcode, provenance, and metadata matches."""

    def aliases(self, term: SearchTerm) -> dict[str, Combinable]:
        """Return internal aliases for each exact-identifier namespace.

        Args:
            term: Normalized user query.

        Returns:
            Boolean ORM expressions keyed by private search alias.
        """

        if term.is_empty:
            return self._empty_aliases()
        return {
            "_search_isbn_hit": self._isbn_hit(term),
            "_search_barcode_hit": self._barcode_hit(term),
            "_search_source_identifier_hit": self._source_identifier_hit(term),
            "_search_external_identifier_hit": self._external_identifier_hit(term),
        }

    @staticmethod
    def _empty_aliases() -> dict[str, Combinable]:
        """Return false aliases for an empty term."""

        return {
            "_search_isbn_hit": false_expression(),
            "_search_barcode_hit": false_expression(),
            "_search_source_identifier_hit": false_expression(),
            "_search_external_identifier_hit": false_expression(),
        }

    @staticmethod
    def _isbn_hit(term: SearchTerm) -> Combinable:
        """Return whether an active edition has the candidate ISBN.

        Args:
            term: Normalized user query.

        Returns:
            A correlated existence expression.
        """

        if not term.permits_isbn or term.exact_isbn is None:
            return false_expression()
        editions = BookEdition.objects.filter(
            work_id=OuterRef("pk"),
            archived_at__isnull=True,
            isbn=term.exact_isbn,
        ).order_by()
        return Exists(editions)

    @staticmethod
    def _barcode_hit(term: SearchTerm) -> Combinable:
        """Return whether an active copy has the candidate barcode.

        Args:
            term: Normalized user query.

        Returns:
            A correlated existence expression.
        """

        if not term.permits_barcode:
            return false_expression()
        copies = (
            BookCopy.objects.filter(
                edition__work_id=OuterRef("pk"),
                edition__archived_at__isnull=True,
                archived_at__isnull=True,
                barcode__iexact=term.text,
            )
            .exclude(status=BookCopyStatus.ARCHIVED)
            .order_by()
        )
        return Exists(copies)

    @staticmethod
    def _source_identifier_hit(term: SearchTerm) -> Combinable:
        """Return whether provenance has the candidate source identifier.

        Args:
            term: Normalized user query.

        Returns:
            A correlated existence expression that ignores archived editions.
        """

        if not term.permits_external_identifier:
            return false_expression()
        work_records = ExternalSourceRecord.objects.filter(
            work_id=OuterRef("pk"),
            source_identifier__iexact=term.text,
        ).order_by()
        edition_records = ExternalSourceRecord.objects.filter(
            edition__work_id=OuterRef("pk"),
            edition__archived_at__isnull=True,
            source_identifier__iexact=term.text,
        ).order_by()
        return Case(
            When(Exists(work_records), then=Value(True)),
            When(Exists(edition_records), then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        )

    @staticmethod
    def _external_identifier_hit(term: SearchTerm) -> Combinable:
        """Return whether active-edition JSON metadata has the candidate ID.

        Text comparison is case-insensitive. A decimal query also checks the
        integer representation because imported JSON may encode identifiers as
        either strings or numbers.

        Args:
            term: Normalized user query.

        Returns:
            A correlated existence expression.
        """

        if not term.permits_external_identifier:
            return false_expression()
        identifier_condition = Q()
        for key in _EXTERNAL_IDENTIFIER_KEYS:
            identifier_condition |= Q(**{f"external_identifiers__{key}__iexact": term.text})
            if term.numeric_identifier is not None:
                identifier_condition |= Q(
                    **{f"external_identifiers__{key}": term.numeric_identifier}
                )
        editions = (
            BookEdition.objects.filter(
                work_id=OuterRef("pk"),
                archived_at__isnull=True,
            )
            .filter(identifier_condition)
            .order_by()
        )
        return Exists(editions)


def any_identifier_hit_expression() -> Case:
    """Return one boolean expression combining all identifier aliases."""

    return Case(
        When(_search_isbn_hit=True, then=Value(True)),
        When(_search_barcode_hit=True, then=Value(True)),
        When(_search_source_identifier_hit=True, then=Value(True)),
        When(_search_external_identifier_hit=True, then=Value(True)),
        default=Value(False),
        output_field=BooleanField(),
    )

"""Lexical catalog search helpers.

This slice stays ORM-only so it works on SQLite in tests and leaves room for a
later PostgreSQL FTS layer without changing the public contract.
"""

from __future__ import annotations

from typing import Final

from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector
from django.core.exceptions import ValidationError
from django.db import connection
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Exists,
    FloatField,
    IntegerField,
    OuterRef,
    Q,
    QuerySet,
    Value,
    When,
)
from django.db.models.functions import Coalesce

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    ExternalSourceRecord,
    WorkContributor,
    clean_isbn,
    normalize_name,
)
from libraryops.circulation.models import Loan
from libraryops.inventory.models import BookCopy, BookCopyStatus

_EXTERNAL_IDENTIFIER_KEYS: Final[tuple[str, ...]] = (
    "openlibrary_work_id",
    "openlibrary_edition_id",
    "openlibrary_id",
    "gutenberg_ebook_id",
    "gutenberg_id",
)


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
    queryset = _apply_facets(
        base_queryset,
        availability=availability,
        contributor=contributor,
        subject=subject,
        language=language,
        source=source,
    )
    normalized_query = " ".join((query or "").strip().split())
    if not normalized_query:
        return queryset

    normalized_phrase = normalize_name(normalized_query)
    exact_isbn = _exact_isbn(normalized_query)

    queryset = queryset.annotate(
        search_isbn_hit=_isbn_hit(exact_isbn),
        search_barcode_hit=_barcode_hit(normalized_query),
        search_external_source_identifier_hit=_external_source_identifier_hit(normalized_query),
        search_edition_external_identifier_hit=_edition_external_identifier_hit(normalized_query),
        search_title_phrase_hit=_title_phrase_hit(normalized_phrase),
        search_contributor_phrase_hit=_contributor_phrase_hit(normalized_phrase),
        search_title_broad_hit=_title_broad_hit(normalized_query),
        search_contributor_broad_hit=_contributor_broad_hit(normalized_query),
    )
    if connection.vendor == "postgresql":
        queryset = queryset.annotate(**_postgres_keyword_annotations(normalized_query))
    else:
        queryset = queryset.annotate(
            search_keyword_rank=Value(0.0, output_field=FloatField()),
        )
    queryset = queryset.annotate(
        search_identifier_hit=Case(
            When(search_isbn_hit=True, then=Value(True)),
            When(search_barcode_hit=True, then=Value(True)),
            When(search_external_source_identifier_hit=True, then=Value(True)),
            When(search_edition_external_identifier_hit=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        search_phrase_hit=Case(
            When(search_title_phrase_hit=True, then=Value(True)),
            When(search_contributor_phrase_hit=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        search_keyword_hit=Case(
            When(search_keyword_rank__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        search_broad_hit=Case(
            When(search_title_broad_hit=True, then=Value(True)),
            When(search_contributor_broad_hit=True, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        search_explanation=Case(
            When(search_identifier_hit=True, then=Value("Exact identifier match")),
            When(search_phrase_hit=True, then=Value("Exact phrase match")),
            When(search_keyword_hit=True, then=Value("Keyword match")),
            When(search_broad_hit=True, then=Value("Broad lexical match")),
            default=Value("Broad lexical match"),
            output_field=CharField(),
        ),
    )
    queryset = queryset.filter(
        Q(search_identifier_hit=True)
        | Q(search_phrase_hit=True)
        | Q(search_keyword_hit=True)
        | Q(search_broad_hit=True)
    )
    return queryset.annotate(
        search_rank=Case(
            When(search_identifier_hit=True, then=Value(0)),
            When(search_phrase_hit=True, then=Value(1)),
            When(search_keyword_hit=True, then=Value(2)),
            When(search_broad_hit=True, then=Value(3)),
            default=Value(4),
            output_field=IntegerField(),
        )
    ).order_by("search_rank", "-search_keyword_rank", "title", "pk")


def _apply_facets(
    queryset: QuerySet[BibliographicWork],
    *,
    availability: str | None,
    contributor: str | None,
    subject: str | None,
    language: str | None,
    source: str | None,
) -> QuerySet[BibliographicWork]:
    """Restrict a catalog queryset by the selected facet values."""

    if contributor:
        queryset = queryset.filter(
            Exists(
                WorkContributor.objects.filter(
                    work=OuterRef("pk"),
                    contributor__normalized_name=normalize_name(contributor),
                )
            )
        )
    if subject:
        subject_lookup = "contains" if connection.vendor == "postgresql" else "icontains"
        queryset = queryset.filter(
            Exists(
                BookEdition.objects.filter(
                    work=OuterRef("pk"),
                    archived_at__isnull=True,
                ).filter(
                    **{
                        f"external_identifiers__subjects__{subject_lookup}": [subject]
                        if subject_lookup == "contains"
                        else subject
                    }
                )
            )
        )
    if language:
        queryset = queryset.filter(
            Exists(
                BookEdition.objects.filter(
                    work=OuterRef("pk"),
                    archived_at__isnull=True,
                    language=language,
                )
            )
        )
    if source:
        queryset = queryset.filter(
            Exists(
                ExternalSourceRecord.objects.filter(
                    Q(work=OuterRef("pk")) | Q(edition__work=OuterRef("pk")),
                    source_name=source,
                )
            )
        )
    if availability:
        queryset = _apply_availability_filter(queryset, availability)
    return queryset


def _apply_availability_filter(
    queryset: QuerySet[BibliographicWork],
    availability: str,
) -> QuerySet[BibliographicWork]:
    """Restrict works by live inventory and circulation state."""

    active_copy_qs = BookCopy.objects.filter(
        edition__work=OuterRef("pk"),
        archived_at__isnull=True,
    )
    available_copy_qs = (
        active_copy_qs.filter(
            status=BookCopyStatus.AVAILABLE.value,
        )
        .annotate(
            has_active_loan=Exists(
                Loan.objects.filter(
                    copy=OuterRef("pk"),
                    returned_at__isnull=True,
                )
            )
        )
        .filter(
            has_active_loan=False,
        )
    )
    queryset = queryset.annotate(
        search_has_active_copy=Exists(active_copy_qs),
        search_has_available_copy=Exists(available_copy_qs),
    )
    if availability == "available":
        return queryset.filter(search_has_available_copy=True)
    if availability == "unavailable":
        return queryset.filter(search_has_active_copy=True, search_has_available_copy=False)
    return queryset


def _postgres_keyword_annotations(query: str) -> dict[str, object]:
    """Return weighted PostgreSQL FTS annotations for one lexical query."""

    return {
        "search_contributor_text": StringAgg(
            "work_contributors__contributor__name",
            delimiter=" ",
            distinct=True,
        ),
        "search_publisher_text": StringAgg(
            "editions__publisher",
            delimiter=" ",
            distinct=True,
        ),
        "search_keyword_rank": Coalesce(
            postgres_keyword_rank_expression(query),
            Value(0.0),
            output_field=FloatField(),
        ),
    }


def postgres_keyword_rank_expression(query: str):
    """Build the weighted PostgreSQL rank expression for one keyword query."""

    search_query = SearchQuery(query, search_type="websearch", config="english")
    search_vector = (
        SearchVector("title", weight="A", config="english")
        + SearchVector("search_contributor_text", weight="A", config="english")
        + SearchVector("search_publisher_text", weight="B", config="english")
        + SearchVector("description", weight="C", config="english")
    )
    return SearchRank(search_vector, search_query)


def _exact_isbn(query: str) -> str | None:
    """Normalize a candidate ISBN for exact matching."""

    try:
        return clean_isbn(query)
    except ValidationError:
        return None


def _isbn_hit(exact_isbn: str | None):
    """Return a boolean expression for an exact ISBN hit."""

    if exact_isbn is None:
        return Value(False, output_field=BooleanField())
    return Exists(
        BookEdition.objects.filter(
            work=OuterRef("pk"),
            archived_at__isnull=True,
            isbn=exact_isbn,
        )
    )


def _barcode_hit(query: str):
    """Return a boolean expression for an exact barcode hit."""

    return Exists(
        BookCopy.objects.filter(
            edition__work=OuterRef("pk"),
            archived_at__isnull=True,
            barcode__iexact=query,
        )
    )


def _external_source_identifier_hit(query: str):
    """Return a boolean expression for exact source-identifier hits."""

    return Exists(
        ExternalSourceRecord.objects.filter(
            Q(work=OuterRef("pk")) | Q(edition__work=OuterRef("pk")),
            source_identifier=query,
        )
    )


def _edition_external_identifier_hit(query: str):
    """Return a boolean expression for exact edition external identifiers."""

    identifier_q = Q()
    for key in _EXTERNAL_IDENTIFIER_KEYS:
        identifier_q |= Q(**{f"external_identifiers__{key}": query})

    return Exists(
        BookEdition.objects.filter(
            work=OuterRef("pk"),
            archived_at__isnull=True,
        ).filter(identifier_q)
    )


def _title_phrase_hit(normalized_phrase: str):
    """Return a boolean expression for exact normalized title hits."""

    return Exists(
        BibliographicWork.objects.filter(pk=OuterRef("pk"), normalized_title=normalized_phrase)
    )


def _contributor_phrase_hit(normalized_phrase: str):
    """Return a boolean expression for exact normalized contributor hits."""

    return Exists(
        WorkContributor.objects.filter(
            work=OuterRef("pk"),
            contributor__normalized_name=normalized_phrase,
        )
    )


def _title_broad_hit(query: str):
    """Return a boolean expression for broader title text hits."""

    return Exists(BibliographicWork.objects.filter(pk=OuterRef("pk"), title__icontains=query))


def _contributor_broad_hit(query: str):
    """Return a boolean expression for broader contributor text hits."""

    return Exists(
        WorkContributor.objects.filter(
            work=OuterRef("pk"),
            contributor__name__icontains=query,
        )
    )

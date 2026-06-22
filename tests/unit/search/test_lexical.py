"""Unit and query-compilation tests for exact-first lexical catalog search."""

from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast

import pytest
from django.contrib.postgres.search import SearchRank
from django.db import connection
from django.db.models import Case, FloatField, Value, When
from django.db.utils import ConnectionHandler
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.catalog import selectors
from libraryops.catalog.models import BibliographicWork, ExternalSourceRecord
from libraryops.inventory.models import BookCopyStatus
from libraryops.search.lexical.backends import PostgresKeywordRankBackend
from libraryops.search.lexical.criteria import (
    CatalogSearchCriteria,
    IdentifierNamespace,
    SearchTerm,
)
from libraryops.search.lexical.engine import CatalogSearchEngine
from libraryops.search.lexical.ranking import DeterministicRankingPolicy

if TYPE_CHECKING:
    from django.db.models import QuerySet
    from django.db.models.expressions import Combinable

    from libraryops.search.lexical.backends import KeywordRankBackend


class RankedWork(Protocol):
    """Describe public annotations added to ranked work instances."""

    pk: int | None
    search_keyword_rank: float
    search_rank: int
    search_explanation: str


@dataclass(frozen=True, slots=True)
class _TitleContainsKeywordBackend:
    """Provide deterministic positive keyword scores for focused tests."""

    def rank_expression(self, term: SearchTerm) -> Combinable:
        """Rank titles containing the normalized query payload.

        Args:
            term: Normalized search term.

        Returns:
            A deterministic floating-point ``CASE`` expression.
        """

        return Case(
            When(title__icontains=term.text, then=Value(1.0)),
            default=Value(0.0),
            output_field=FloatField(),
        )


@dataclass(frozen=True, slots=True)
class _StaticBackendSelector:
    """Return one injected keyword backend regardless of database vendor."""

    backend: KeywordRankBackend

    def resolve(self, queryset: QuerySet[BibliographicWork]) -> KeywordRankBackend:
        """Return the configured backend.

        Args:
            queryset: Queryset accepted to satisfy the resolver protocol.

        Returns:
            The configured keyword backend.
        """

        _ = queryset
        return self.backend


class CatalogLexicalSearchTests(TestCase):
    """Prove exact identifiers, phrases, facets, and fallback behavior."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed exact matches, broad distractors, facets, and archived rows."""

        cls.exact_work = WorkContributorFactory(
            work__title="Pride and Prejudice",
            work__description="A novel about manners and social class.",
            contributor__name="Jane Austen",
        ).work
        cls.exact_edition = BookEditionFactory(
            work=cls.exact_work,
            publisher="T. Egerton",
            description="Classic English literature.",
            isbn="9780141439518",
            language="en",
            external_identifiers={
                "openlibrary_work_id": "OL1W",
                "gutenberg_ebook_id": 1342,
                "subjects": ["Classics", "Romance"],
            },
        )
        BookCopyFactory(edition=cls.exact_edition, barcode="BC-1001")
        ExternalSourceRecord.objects.create(
            source_name="openlibrary",
            source_identifier="OL1W",
            source_url="https://openlibrary.org/works/OL1W",
            work=cls.exact_work,
        )

        cls.identifier_distractor = WorkContributorFactory(
            work__title="Reference 9780141439518 BC-1001 OL1W 1342",
            contributor__name="Broader Author",
        ).work
        BookEditionFactory(work=cls.identifier_distractor, isbn=build_isbn13(2))

        cls.broad_work = WorkContributorFactory(
            work__title="Pride and Prejudice Annotated",
            work__description="Critical commentary.",
            contributor__name="Jane Austen Society",
        ).work
        cls.broad_edition = BookEditionFactory(
            work=cls.broad_work,
            publisher="Essay House",
            description="Literary criticism.",
            isbn=build_isbn13(3),
            language="fr",
            external_identifiers={"subjects": ["Essays"]},
        )
        cls.broad_copy = BookCopyFactory(
            edition=cls.broad_edition,
            barcode="BC-2001",
        )
        cls.broad_copy.status = BookCopyStatus.ON_LOAN.value
        cls.broad_copy.save(update_fields=["status", "updated_at"])
        ExternalSourceRecord.objects.create(
            source_name="gutenberg",
            source_identifier="PG-ESSAYS",
            source_url="https://www.gutenberg.org/ebooks/2001",
            edition=cls.broad_edition,
        )

        cls.cross_field_work = WorkContributorFactory(
            work__title="Cross-field Search",
            work__description="A portable fallback fixture.",
            contributor__name="Grace Hopper",
        ).work
        cls.cross_field_edition = BookEditionFactory(
            work=cls.cross_field_work,
            publisher="Compiler Press",
            description="Distributed systems handbook.",
            isbn=build_isbn13(4),
            language="en",
            external_identifiers={"subjects": ["Computing"]},
        )
        cls.cross_field_copy = BookCopyFactory(
            edition=cls.cross_field_edition,
            barcode="BC-3001",
        )
        cls.cross_field_copy.status = BookCopyStatus.MAINTENANCE.value
        cls.cross_field_copy.save(update_fields=["status", "updated_at"])

        archived_at = timezone.now()
        cls.archived_edition = BookEditionFactory(
            work=cls.exact_work,
            publisher="Archived Press",
            description="Archived-only metadata.",
            isbn=build_isbn13(5),
            language="de",
            external_identifiers={
                "openlibrary_id": "ARCHIVED-OL-ID",
                "subjects": ["Archived Subject"],
            },
            archived_at=archived_at,
        )
        BookCopyFactory(
            edition=cls.archived_edition,
            barcode="ARCHIVED-COPY",
            status=BookCopyStatus.ARCHIVED,
            archived_at=archived_at,
        )
        ExternalSourceRecord.objects.create(
            source_name="openlibrary-archive",
            source_identifier="ARCHIVED-SOURCE",
            edition=cls.archived_edition,
        )

    @staticmethod
    def _search_with_keyword_backend(query: str) -> QuerySet[BibliographicWork]:
        """Return search results using the deterministic test backend.

        Args:
            query: Free text or identifier query.

        Returns:
            A lazy ranked work queryset.
        """

        engine = CatalogSearchEngine(
            backend_selector=_StaticBackendSelector(_TitleContainsKeywordBackend())
        )
        return engine.search(
            BibliographicWork.objects.foundation_index(),
            CatalogSearchCriteria.from_values(query),
        )

    def test_search_construction_is_lazy(self) -> None:
        """Building a search queryset must not execute SQL."""

        criteria = CatalogSearchCriteria.from_values("Pride and Prejudice")
        with CaptureQueriesContext(connection) as captured:
            queryset = CatalogSearchEngine().search(
                BibliographicWork.objects.foundation_index(),
                criteria,
            )
        assert captured.captured_queries == []
        assert queryset.query is not None

    def test_exact_identifiers_rank_ahead_of_keyword_distractors(self) -> None:
        """Qualified and unqualified identifiers always occupy tier zero."""

        for query in (
            "9780141439518",
            "isbn:9780141439518",
            "bc-1001",
            "barcode:bc-1001",
            "ol1w",
            "source:ol1w",
            "1342",
            "id:1342",
        ):
            with self.subTest(query=query):
                results = [
                    cast("RankedWork", work) for work in self._search_with_keyword_backend(query)
                ]
                assert results[0].pk == self.exact_work.pk
                assert results[0].search_rank == 0
                assert results[0].search_explanation == "Exact identifier match"
                assert results[1].pk == self.identifier_distractor.pk
                assert results[1].search_rank == 2
                assert results[1].search_explanation == "Keyword match"

    def test_identifier_prefix_restricts_unrelated_exact_namespaces(self) -> None:
        """A qualifier prevents the payload matching another identifier type."""

        assert (
            not selectors.work_list(query="barcode:9780141439518")
            .filter(pk=self.exact_work.pk)
            .exists()
        )
        assert not selectors.work_list(query="isbn:BC-1001").filter(pk=self.exact_work.pk).exists()

    def test_exact_phrases_rank_ahead_of_broad_matches(self) -> None:
        """Exact normalized title and contributor equality occupy tier one."""

        for query in ("Pride and Prejudice", "Jane Austen"):
            with self.subTest(query=query):
                results = [cast("RankedWork", work) for work in selectors.work_list(query=query)]
                assert results[0].pk == self.exact_work.pk
                assert results[0].search_rank == 1
                assert results[0].search_explanation == "Exact phrase match"
                assert self.broad_work.pk in {work.pk for work in results[1:]}

    def test_keyword_explanation_stays_aligned_with_keyword_tier(self) -> None:
        """A positive backend score produces the keyword tier and explanation."""

        results = [
            cast("RankedWork", work)
            for work in self._search_with_keyword_backend("Pride and Prejudice")
        ]
        assert results[0].pk == self.exact_work.pk
        assert results[0].search_explanation == "Exact phrase match"
        assert results[1].pk == self.broad_work.pk
        assert results[1].search_rank == 2
        assert results[1].search_explanation == "Keyword match"

    def test_portable_fallback_requires_every_token_across_fields(self) -> None:
        """SQLite broad search approximates web-search AND semantics."""

        result_ids = list(
            selectors.work_list(query="Grace Compiler distributed").values_list(
                "pk",
                flat=True,
            )
        )
        assert result_ids == [self.cross_field_work.pk]
        assert not selectors.work_list(query="Grace missing-token").exists()

    def test_facets_compose_without_free_text(self) -> None:
        """All facets compose over live catalog, inventory, and provenance data."""

        result_ids = list(
            selectors.work_list(
                availability=" AVAILABLE ",
                contributor="  Jane   Austen ",
                subject="Classics",
                language="EN",
                source="OpenLibrary",
            ).values_list("pk", flat=True)
        )
        assert result_ids == [self.exact_work.pk]

    def test_availability_uses_active_copy_and_edition_state(self) -> None:
        """Unavailable means inventory exists but no active available copy."""

        available_ids = set(
            selectors.work_list(availability="available").values_list("pk", flat=True)
        )
        unavailable_ids = set(
            selectors.work_list(availability="unavailable").values_list("pk", flat=True)
        )
        assert self.exact_work.pk in available_ids
        assert self.broad_work.pk in unavailable_ids
        assert self.cross_field_work.pk in unavailable_ids

    def test_archived_edition_identifiers_and_facets_are_ignored(self) -> None:
        """Archived editions cannot satisfy identifier, source, or facet paths."""

        for query in (
            build_isbn13(5),
            "barcode:ARCHIVED-COPY",
            "id:ARCHIVED-OL-ID",
            "source:ARCHIVED-SOURCE",
        ):
            with self.subTest(query=query):
                assert not selectors.work_list(query=query).exists()
        assert not selectors.work_list(subject="Archived Subject").exists()
        assert not selectors.work_list(language="de").exists()
        assert not selectors.work_list(source="openlibrary-archive").exists()

    def test_correlated_subqueries_do_not_duplicate_work_rows(self) -> None:
        """Multiple related rows still produce one outer work result."""

        WorkContributorFactory(
            work=self.exact_work,
            contributor__name="Jane B. Austen",
        )
        BookEditionFactory(
            work=self.exact_work,
            publisher="Second Publisher",
            isbn=build_isbn13(6),
        )
        result_ids = list(selectors.work_list(query="Pride").values_list("pk", flat=True))
        assert result_ids.count(self.exact_work.pk) == 1

    def test_blank_and_nonlexical_queries_are_safe(self) -> None:
        """Blank criteria preserve facets and punctuation-only text finds nothing."""

        criteria = CatalogSearchCriteria.from_values("   ", availability="unsupported")
        assert criteria.term.is_empty
        assert criteria.facets.availability is None
        result_ids = set(
            selectors.work_list(query="   ", language="fr").values_list("pk", flat=True)
        )
        assert result_ids == {self.broad_work.pk}
        assert not selectors.work_list(query="---").exists()


def test_criteria_objects_are_normalized_and_immutable() -> None:
    """Criteria collapse whitespace, parse qualifiers, and cannot be mutated."""

    criteria = CatalogSearchCriteria.from_values(
        "  barcode :  COPY-0001  ",
        contributor="  Jane   Austen ",
    )
    assert criteria.term.text == "COPY-0001"
    assert criteria.term.normalized_phrase == "copy-0001"
    assert criteria.term.tokens == ("copy", "0001")
    assert criteria.term.identifier_namespace is IdentifierNamespace.BARCODE
    assert criteria.facets.contributor == "Jane Austen"
    with pytest.raises(FrozenInstanceError):
        criteria.term.text = "changed"  # type: ignore[misc]


def test_oversized_numeric_identifier_is_not_converted_to_an_integer() -> None:
    """Hostile-size decimal input remains safe and available for text matching."""

    value = "9" * 10_000
    term = SearchTerm.from_value(value)

    assert term.text == value
    assert term.numeric_identifier is None


def test_postgresql_query_compiles_with_independent_aggregate_subqueries() -> None:
    """PostgreSQL SQL uses weighted FTS without outer join multiplication."""

    term = SearchTerm.from_value("Jane classics Egerton")
    queryset = DeterministicRankingPolicy().apply(
        BibliographicWork.objects.all(),
        term,
        keyword_backend=PostgresKeywordRankBackend(),
    )
    handler = ConnectionHandler(
        {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": "compile_only",
                "USER": "compile_only",
                "PASSWORD": "compile_only",
                "HOST": "127.0.0.1",
                "PORT": "1",
            }
        }
    )
    sql, parameters = queryset.query.get_compiler(connection=handler["default"]).as_sql()
    normalized_sql = sql.upper()
    assert "WEBSEARCH_TO_TSQUERY" in normalized_sql
    assert "TS_RANK" in normalized_sql
    assert normalized_sql.count("STRING_AGG") >= 4
    outer_from = normalized_sql.rsplit(
        ' FROM "CATALOG_BIBLIOGRAPHICWORK"',
        maxsplit=1,
    )[1].split(" WHERE ", maxsplit=1)[0]
    assert "JOIN" not in outer_from
    assert "GROUP BY" not in outer_from
    assert "english" in parameters
    assert set(queryset.query.annotation_select) == {
        "search_keyword_rank",
        "search_rank",
        "search_explanation",
        "search_availability_state",
        "search_matched_identifier_value",
    }
    assert isinstance(PostgresKeywordRankBackend().rank_expression(term), SearchRank)


def test_search_package_uses_split_modules_and_preserves_public_facade() -> None:
    """The package conversion removes the flat module but keeps the top-level facade."""

    import libraryops.search as search_package
    import libraryops.search.lexical as lexical_package

    search_root = Path(search_package.__file__).resolve().parent
    assert not (search_root / "lexical.py").exists()
    assert hasattr(search_package, "search_catalog")
    assert not hasattr(lexical_package, "search_catalog")
    assert not hasattr(lexical_package, "CatalogSearchEngine")
    assert not hasattr(lexical_package, "CatalogSearchCriteria")

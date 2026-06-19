"""Unit tests for lexical catalog search ranking."""

from __future__ import annotations

from typing import Any, cast
from unittest.mock import patch

from django.contrib.postgres.search import SearchRank
from django.db.models import Case, FloatField, Value, When
from django.test import TestCase
from tests.factories import (
    BookCopyFactory,
    BookEditionFactory,
    LoanFactory,
    WorkContributorFactory,
    build_isbn13,
)

from libraryops.catalog import selectors
from libraryops.catalog.models import ExternalSourceRecord
from libraryops.search.lexical import postgres_keyword_rank_expression


class CatalogLexicalSearchTests(TestCase):
    """Prove exact identifiers and exact phrases outrank broader matches."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed one exact-hit work and broad title/contributor distractors."""

        cls.exact_work = WorkContributorFactory(
            work__title="Exact Match Work",
            contributor__name="Exact Author",
        ).work
        cls.exact_edition = BookEditionFactory(
            work=cls.exact_work,
            isbn="9780141439518",
            language="en",
            external_identifiers={
                "openlibrary_work_id": "OL1W",
                "gutenberg_ebook_id": "1342",
                "subjects": ["Classics"],
            },
        )
        BookCopyFactory(edition=cls.exact_edition, barcode="BC-1001")
        ExternalSourceRecord.objects.create(
            source_name="openlibrary",
            source_identifier="OL1W",
            source_url="https://openlibrary.org/works/OL1W",
            work=cls.exact_work,
        )

        cls.broad_identifier_work = WorkContributorFactory(
            work__title="Reference 9780141439518 BC-1001 OL1W 1342",
            contributor__name="Broader Author",
        ).work
        BookEditionFactory(work=cls.broad_identifier_work, isbn=build_isbn13(2))

        cls.exact_title_work = WorkContributorFactory(
            work__title="Pride and Prejudice",
            contributor__name="Title Author",
        ).work
        BookEditionFactory(work=cls.exact_title_work, isbn=build_isbn13(3))

        cls.broad_title_work = WorkContributorFactory(
            work__title="Pride and Prejudice Annotated",
            contributor__name="Title Author 2",
        ).work
        BookEditionFactory(work=cls.broad_title_work, isbn=build_isbn13(4))

        cls.exact_author_work = WorkContributorFactory(
            work__title="Author Exact Work",
            contributor__name="Jane Austen",
        ).work
        BookEditionFactory(work=cls.exact_author_work, isbn=build_isbn13(5))

        cls.broad_author_work = WorkContributorFactory(
            work__title="Author Broad Work",
            contributor__name="Jane Austen Society",
        ).work
        BookEditionFactory(work=cls.broad_author_work, isbn=build_isbn13(6))

        cls.unavailable_work = WorkContributorFactory(
            work__title="Unavailable Filter Work",
            contributor__name="Unavailable Author",
        ).work
        cls.unavailable_edition = BookEditionFactory(
            work=cls.unavailable_work,
            isbn=build_isbn13(7),
            language="fr",
            external_identifiers={"subjects": ["History"]},
        )
        cls.unavailable_copy = BookCopyFactory(
            edition=cls.unavailable_edition,
            barcode="BC-2001",
        )
        LoanFactory(copy=cls.unavailable_copy)
        ExternalSourceRecord.objects.create(
            source_name="gutenberg",
            source_identifier="2001",
            source_url="https://www.gutenberg.org/ebooks/2001",
            edition=cls.unavailable_edition,
        )

    @patch("libraryops.search.lexical.connection.vendor", "postgresql")
    def test_exact_identifiers_rank_ahead_of_keyword_matches(self) -> None:
        """ISBN, barcode, Open Library, and Gutenberg hits should outrank keyword hits."""

        def _keyword_rank_expression(_query: str) -> Case:
            return Case(
                When(title__icontains=query, then=Value(1.0)),
                default=Value(0.0),
                output_field=FloatField(),
            )

        def _keyword_annotations(query: str) -> dict[str, Any]:
            return {
                "search_contributor_text": Value(""),
                "search_publisher_text": Value(""),
                "search_keyword_rank": _keyword_rank_expression(query),
            }

        with patch(
            "libraryops.search.lexical._postgres_keyword_annotations",
            side_effect=_keyword_annotations,
        ):
            for query in ("9780141439518", "BC-1001", "OL1W", "1342"):
                with self.subTest(query=query):
                    results = list(selectors.work_list(query=query))
                    assert results[0].pk == self.exact_work.pk
                    assert cast("Any", results[0]).search_explanation == "Exact identifier match"
                    assert results[1].pk == self.broad_identifier_work.pk
                    assert cast("Any", results[1]).search_explanation == "Keyword match"

    def test_exact_title_phrase_ranks_ahead_of_broader_title_text_hits(self) -> None:
        """An exact normalized title phrase should outrank a looser title match."""

        results = list(selectors.work_list(query="Pride and Prejudice"))

        assert results[0].pk == self.exact_title_work.pk
        assert cast("Any", results[0]).search_explanation == "Exact phrase match"
        assert self.broad_title_work.pk in [work.pk for work in results]
        assert cast("Any", results[1]).search_explanation == "Broad lexical match"

    def test_exact_author_phrase_ranks_ahead_of_broader_author_text_hits(self) -> None:
        """An exact normalized contributor phrase should outrank a looser contributor match."""

        results = list(selectors.work_list(query="Jane Austen"))

        assert results[0].pk == self.exact_author_work.pk
        assert cast("Any", results[0]).search_explanation == "Exact phrase match"
        assert self.broad_author_work.pk in [work.pk for work in results]
        assert cast("Any", results[1]).search_explanation == "Broad lexical match"

    @patch("libraryops.search.lexical.connection.vendor", "postgresql")
    def test_keyword_match_explanation_is_stable(self) -> None:
        """A keyword-ranked result should carry the keyword explanation text."""

        def _keyword_rank_expression(_query: str) -> Case:
            return Case(
                When(title__icontains="Annotated", then=Value(1.0)),
                default=Value(0.0),
                output_field=FloatField(),
            )

        def _keyword_annotations(query: str) -> dict[str, Any]:
            return {
                "search_contributor_text": Value(""),
                "search_publisher_text": Value(""),
                "search_keyword_rank": _keyword_rank_expression(query),
            }

        with patch(
            "libraryops.search.lexical._postgres_keyword_annotations",
            side_effect=_keyword_annotations,
        ):
            results = list(selectors.work_list(query="Pride and Prejudice"))

        assert results[0].pk == self.exact_title_work.pk
        assert cast("Any", results[0]).search_explanation == "Exact phrase match"
        assert results[1].pk == self.broad_title_work.pk
        assert cast("Any", results[1]).search_explanation == "Keyword match"

    def test_facets_filter_live_catalog_inventory_and_provenance_state(self) -> None:
        """Facet helpers should filter by live catalog, inventory, and provenance data."""

        results = list(
            selectors.work_list(
                availability="available",
                contributor="Exact Author",
                subject="Classics",
                language="en",
                source="openlibrary",
            )
        )

        assert [work.pk for work in results] == [self.exact_work.pk]

    def test_availability_filter_uses_active_loan_state(self) -> None:
        """Availability filtering should exclude works with active loans."""

        available_results = list(selectors.work_list(availability="available"))
        unavailable_results = list(selectors.work_list(availability="unavailable"))

        assert self.exact_work.pk in [work.pk for work in available_results]
        assert self.unavailable_work.pk not in [work.pk for work in available_results]
        assert self.unavailable_work.pk in [work.pk for work in unavailable_results]

    @patch("libraryops.search.lexical.connection.vendor", "postgresql")
    def test_postgresql_branch_adds_weighted_keyword_rank_annotations(self) -> None:
        """The PostgreSQL branch should add the weighted keyword rank annotation."""

        queryset = selectors.work_list(query="Pride and Prejudice")

        assert "search_contributor_text" in queryset.query.annotations
        assert "search_publisher_text" in queryset.query.annotations
        assert "search_keyword_rank" in queryset.query.annotations
        assert "search_explanation" in queryset.query.annotations
        rank_expression = postgres_keyword_rank_expression("Pride and Prejudice")
        assert isinstance(rank_expression, SearchRank)
        assert "search_contributor_text" in str(rank_expression)
        assert "search_publisher_text" in str(rank_expression)

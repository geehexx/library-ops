"""Tests for catalog selector helpers."""

from __future__ import annotations

from django.test import TestCase
from django.utils import timezone
from tests.factories import (
    BibliographicWorkFactory,
    BookCopyFactory,
    BookEditionFactory,
    LoanFactory,
)

from libraryops.catalog.selectors import work_facet_options, work_list
from libraryops.inventory.models import BookCopyStatus


class CatalogSelectorTests(TestCase):
    """Cover subject aggregation from edition provenance metadata."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Seed works with mixed subject payloads."""

        cls.first_work = BibliographicWorkFactory(title="First Work")
        cls.second_work = BibliographicWorkFactory(title="Second Work")
        BookEditionFactory(
            work=cls.first_work,
            external_identifiers={
                "subjects": ["  History  ", "Classics", "", "History", None],
            },
        )
        BookEditionFactory(
            work=cls.first_work,
            external_identifiers={"subjects": "Biography"},
        )
        BookEditionFactory(
            work=cls.second_work,
            archived_at=timezone.now(),
            external_identifiers={"subjects": ["Ignored"]},
        )

    def test_work_facet_options_deduplicates_and_normalizes_subjects(self) -> None:
        """The subject facet should return stable, trimmed, case-folded labels."""

        assert work_facet_options()["subjects"] == ["Biography", "Classics", "History"]

    def test_work_list_annotates_available_and_on_loan_copy_counts(self) -> None:
        """The catalog index queryset should expose evaluator-facing availability counts."""

        available_work = BibliographicWorkFactory(title="Available Work")
        available_edition = BookEditionFactory(work=available_work)
        BookCopyFactory(edition=available_edition)

        unavailable_work = BibliographicWorkFactory(title="Unavailable Work")
        unavailable_edition = BookEditionFactory(work=unavailable_work)
        on_loan_copy = BookCopyFactory(edition=unavailable_edition)
        LoanFactory(copy=on_loan_copy)
        on_loan_copy.status = BookCopyStatus.ON_LOAN
        on_loan_copy.save(update_fields=["status"])

        works = {work.title: work for work in work_list()}

        available_row = works["Available Work"]
        unavailable_row = works["Unavailable Work"]

        assert available_row.available_copy_count == 1
        assert available_row.on_loan_copy_count == 0
        assert unavailable_row.available_copy_count == 0
        assert unavailable_row.on_loan_copy_count == 1

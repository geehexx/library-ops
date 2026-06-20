"""Tests for catalog selector helpers."""

from __future__ import annotations

from django.test import TestCase
from django.utils import timezone
from tests.factories import BibliographicWorkFactory, BookEditionFactory

from libraryops.catalog.selectors import work_facet_options


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

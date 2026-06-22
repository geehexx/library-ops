"""Metamorphic properties for lexical normalization and exact ranking.

These properties compare semantically equivalent public queries over a fixed,
purpose-built corpus.  They do not reproduce the search score expression, so a
shared implementation defect cannot make both the system and oracle agree.
"""

from __future__ import annotations

from typing import ClassVar

import pytest
from hypothesis import event, example, given, settings, target
from hypothesis.extra.django import TestCase as HypothesisDjangoTestCase
from tests.property.strategies import isbn13_format_variants, lexical_query_variants

from libraryops.catalog.models import (
    BibliographicWork,
    BookEdition,
    Contributor,
    ContributorRole,
    WorkContributor,
)
from libraryops.inventory.models import BookCopy, BookCopyStatus
from libraryops.search import search_catalog

pytestmark = pytest.mark.property

_TARGET_TITLE = "Property Atlas Quasar"
_TARGET_AUTHOR = "Ada Property"
_TARGET_ISBN = "9780306406157"
_TARGET_BARCODE = "PBT-SEARCH-0001"


class TestLexicalSearchMetamorphicProperties(HypothesisDjangoTestCase):
    """Verify stable public ranking across generated equivalent spellings."""

    target_work_id: ClassVar[int]

    @classmethod
    def setUpTestData(cls) -> None:
        """Create exact targets and broad distractors with no randomized fixture data."""
        target = BibliographicWork.objects.create(title=_TARGET_TITLE)
        target_author = Contributor.objects.create(name=_TARGET_AUTHOR)
        WorkContributor.objects.create(
            work=target,
            contributor=target_author,
            role=ContributorRole.AUTHOR,
            sort_order=0,
        )
        target_edition = BookEdition.objects.create(work=target, isbn=_TARGET_ISBN)
        BookCopy.objects.create(
            edition=target_edition,
            barcode=_TARGET_BARCODE,
            status=BookCopyStatus.AVAILABLE,
        )

        title_distractor = BibliographicWork.objects.create(title=f"{_TARGET_TITLE} Companion")
        unrelated_author = Contributor.objects.create(name="Unrelated Catalog Author")
        WorkContributor.objects.create(
            work=title_distractor,
            contributor=unrelated_author,
            role=ContributorRole.AUTHOR,
            sort_order=0,
        )

        author_distractor = BibliographicWork.objects.create(title="A Separate Property Work")
        broad_author = Contributor.objects.create(name=f"{_TARGET_AUTHOR}son")
        WorkContributor.objects.create(
            work=author_distractor,
            contributor=broad_author,
            role=ContributorRole.AUTHOR,
            sort_order=0,
        )

        isbn_text_distractor = BibliographicWork.objects.create(
            title=f"Guide to {_TARGET_ISBN} identifiers"
        )
        WorkContributor.objects.create(
            work=isbn_text_distractor,
            contributor=unrelated_author,
            role=ContributorRole.EDITOR,
            sort_order=0,
        )

        cls.target_work_id = int(_saved_work_id(target))

    @staticmethod
    def _ordered_ids(query: str) -> list[int]:
        """Materialize ordered work IDs from the public search facade."""
        return [int(pk) for pk in search_catalog(query=query).values_list("pk", flat=True)]

    @example(query=_TARGET_TITLE)
    @settings(deadline=None)
    @given(query=lexical_query_variants(_TARGET_TITLE))
    def test_title_case_and_whitespace_noise_preserve_order(self, query: str) -> None:
        """Equivalent title queries must preserve membership and deterministic order."""
        baseline = self._ordered_ids(_TARGET_TITLE)
        noisy = self._ordered_ids(query)

        assert len(baseline) >= 2
        assert noisy == baseline
        assert noisy[0] == self.target_work_id
        assert self._ordered_ids(query) == noisy

        target(sum(character.isspace() for character in query), label="whitespace_characters")
        event(f"query_length={len(query)}")

    @example(query=_TARGET_AUTHOR)
    @settings(deadline=None)
    @given(query=lexical_query_variants(_TARGET_AUTHOR))
    def test_contributor_case_and_whitespace_noise_preserve_order(self, query: str) -> None:
        """Equivalent contributor queries must retain exact-phrase precedence."""
        baseline = self._ordered_ids(_TARGET_AUTHOR)
        noisy = self._ordered_ids(query)

        assert len(baseline) >= 2
        assert noisy == baseline
        assert noisy[0] == self.target_work_id

    @example(query="978-0-306-40615-7")
    @settings(deadline=None)
    @given(query=isbn13_format_variants(_TARGET_ISBN))
    def test_formatted_exact_isbn_always_ranks_the_target_first(self, query: str) -> None:
        """Supported ISBN formatting must retain exact-identifier precedence."""
        results = self._ordered_ids(query)

        assert results
        assert results[0] == self.target_work_id
        assert self._ordered_ids(query) == results
        event(f"separator_count={sum(character in ' -' for character in query)}")


def _saved_work_id(work: BibliographicWork) -> int:
    """Return the primary key for one persisted work."""
    assert work.pk is not None
    return int(work.pk)

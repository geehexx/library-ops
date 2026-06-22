"""Properties for ISBN validation, normalization, and persistence.

Expected check digits come from the independent oracle in
``tests.property.strategies.isbn``. The tests therefore detect checksum defects
instead of reproducing production logic inside the assertion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from django.core.exceptions import ValidationError
from hypothesis import event, example, given, settings
from hypothesis.extra.django import TestCase as HypothesisDjangoTestCase
from tests.property.strategies import ISBNCase, invalid_checksum_cases, valid_isbn_cases

from libraryops.catalog.models import BibliographicWork, BookEdition, clean_isbn

if TYPE_CHECKING:
    from tests.property.strategies import InvalidISBNCase

pytestmark = pytest.mark.property


@example(
    case=ISBNCase(
        raw="080442957X",
        compact_input="080442957X",
        canonical13="9780804429573",
        kind="isbn10",
    )
)
@example(
    case=ISBNCase(
        raw="0-306-40615-2",
        compact_input="0306406152",
        canonical13="9780306406157",
        kind="isbn10",
    )
)
@example(
    case=ISBNCase(
        raw="978-0-306-40615-7",
        compact_input="9780306406157",
        canonical13="9780306406157",
        kind="isbn13",
    )
)
@given(case=valid_isbn_cases())
def test_valid_isbns_normalize_to_the_independent_canonical_value(case: ISBNCase) -> None:
    """Every valid formatted ISBN should map to one stable ISBN-13 identity."""
    event(f"source_kind={case.kind}")

    normalized = clean_isbn(case.raw)

    assert normalized == case.canonical13
    assert len(normalized) == 13
    assert normalized.isascii()
    assert normalized.isdigit()
    assert clean_isbn(case.compact_input) == normalized
    assert clean_isbn(normalized) == normalized


@given(case=invalid_checksum_cases())
def test_invalid_check_digits_are_never_accepted(case: InvalidISBNCase) -> None:
    """Changing only the check digit must make an ISBN invalid."""
    event(f"source_kind={case.kind}")

    with pytest.raises(ValidationError):
        clean_isbn(case.raw)


class TestBookEditionISBNProperties(HypothesisDjangoTestCase):
    """Verify that the database boundary preserves the pure ISBN contract."""

    @settings(deadline=None)
    @given(case=valid_isbn_cases())
    def test_persistence_stores_canonical_isbn13(self, case: ISBNCase) -> None:
        """Saving a compact valid ISBN should persist canonical digits.

        The model field itself is capped at thirteen characters, so persistence
        covers compact ISBN-10/ISBN-13 values after form- or command-layer
        whitespace/hyphen stripping rather than every raw formatting variant.
        """
        work = BibliographicWork.objects.create(title="ISBN property work")
        edition = BookEdition.objects.create(work=work, isbn=case.compact_input)

        edition.refresh_from_db()

        assert edition.isbn == case.canonical13

    @settings(deadline=None)
    @given(case=invalid_checksum_cases())
    def test_persistence_rejects_invalid_checksums(self, case: InvalidISBNCase) -> None:
        """Model persistence must not bypass ISBN checksum validation."""
        work = BibliographicWork.objects.create(title="Invalid ISBN property work")

        with pytest.raises(ValidationError):
            BookEdition.objects.create(work=work, isbn=case.raw)

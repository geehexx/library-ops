"""Tests for catalog model normalization and validation."""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError
from django.test import TestCase
from hypothesis import given
from hypothesis import strategies as st
from tests.factories import BibliographicWorkFactory

from libraryops.catalog.models import BookEdition, clean_isbn

VALID_ISBN_CASES = [
    ("0743273567", "9780743273565"),
    ("0-7432-7356-7", "9780743273565"),
    ("9780141439518", "9780141439518"),
]


class BookEditionModelTests(TestCase):
    """Cover ISBN normalization and rejection."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Create the work used by edition model tests."""

        cls.work = BibliographicWorkFactory(title="Example Title")

    def test_clean_isbn_normalizes_known_valid_inputs(self) -> None:
        """Ensure valid ISBN inputs normalize to a stable ISBN-13 string."""

        case_ids = ["isbn10-digits", "isbn10-hyphenated", "isbn13"]
        for case_id, (raw_value, normalized_value) in zip(case_ids, VALID_ISBN_CASES, strict=True):
            with self.subTest(case=case_id):
                assert clean_isbn(raw_value) == normalized_value

    def test_clean_isbn_rejects_invalid_values(self) -> None:
        """Ensure invalid ISBN inputs fail validation."""

        for value in ("", "not-an-isbn", "9780743273560"):
            with pytest.raises(ValidationError):
                clean_isbn(value)

    def test_book_edition_persists_normalized_isbn(self) -> None:
        """Ensure model persistence stores the normalized ISBN-13 value."""

        edition = BookEdition.objects.create(work=self.work, isbn="0-7432-7356-7")

        assert edition.isbn == "9780743273565"


@pytest.mark.property
@given(st.sampled_from([case[1] for case in VALID_ISBN_CASES]))
def test_clean_isbn_is_idempotent_for_normalized_values(normalized_value: str) -> None:
    """Ensure already-normalized ISBN-13 values stay stable when re-cleaned."""

    assert clean_isbn(clean_isbn(normalized_value)) == normalized_value

"""Tests for catalog model normalization and validation."""

from __future__ import annotations

from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from hypothesis import given
from hypothesis import strategies as st
from PIL import Image
from tests.factories import BibliographicWorkFactory

import libraryops.catalog.managers as catalog_managers
import libraryops.catalog.models as catalog_models
import libraryops.catalog.querysets as catalog_querysets
from libraryops.catalog.models import (
    EDITION_COVER_MAX_UPLOAD_BYTES,
    BookEdition,
    clean_isbn,
)


def _cover_upload(filename: str, format_name: str) -> SimpleUploadedFile:
    """Build one small in-memory image upload for validation tests."""

    buffer = BytesIO()
    Image.new("RGB", (4, 4), color=(64, 96, 128)).save(buffer, format=format_name)
    content_type = f"image/{format_name.lower()}"
    return SimpleUploadedFile(filename, buffer.getvalue(), content_type=content_type)


def _oversized_cover_upload() -> SimpleUploadedFile:
    """Build one valid image payload that exceeds the configured size limit."""

    upload = _cover_upload("oversized.png", "PNG")
    payload = upload.read()
    padding = b"0" * (EDITION_COVER_MAX_UPLOAD_BYTES - len(payload) + 1)
    upload.seek(0)
    upload_name = upload.name or "oversized.png"
    upload_content_type = upload.content_type or "image/png"
    return SimpleUploadedFile(
        upload_name,
        payload + padding,
        content_type=upload_content_type,
    )

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

    def test_clean_isbn_rejects_invalid_values(self) -> None:
        """Ensure invalid ISBN inputs fail validation."""

        for value in ("", "not-an-isbn", "9780743273560"):
            with pytest.raises(ValidationError):
                clean_isbn(value)

    def test_book_edition_persists_normalized_isbn(self) -> None:
        """Ensure model persistence stores the normalized ISBN-13 value."""

        edition = BookEdition.objects.create(work=self.work, isbn="0-7432-7356-7")

        assert edition.isbn == "9780743273565"

    def test_book_edition_rejects_unsupported_cover_image_types(self) -> None:
        """Ensure only JPEG, PNG, and WebP uploads are accepted."""

        with pytest.raises(ValidationError):
            BookEdition.objects.create(work=self.work, cover_image=_cover_upload("cover.gif", "GIF"))

    def test_book_edition_rejects_oversized_cover_images(self) -> None:
        """Ensure oversized cover uploads fail before persistence."""

        with pytest.raises(ValidationError):
            BookEdition.objects.create(
                work=self.work,
                cover_image=_oversized_cover_upload(),
            )


@pytest.mark.parametrize(
    ("raw_value", "normalized_value"),
    VALID_ISBN_CASES,
    ids=("isbn10-digits", "isbn10-hyphenated", "isbn13"),
)
def test_clean_isbn_normalizes_known_valid_inputs(
    raw_value: str,
    normalized_value: str,
) -> None:
    """Ensure valid ISBN inputs normalize to a stable ISBN-13 string."""

    assert clean_isbn(raw_value) == normalized_value


@pytest.mark.parametrize(
    "module",
    [
        catalog_models,
        catalog_managers,
        catalog_querysets,
    ],
)
def test_catalog_non_facade_modules_do_not_define_all(module: object) -> None:
    """Ensure non-facade catalog modules do not declare export lists."""

    assert not hasattr(module, "__all__")


@pytest.mark.property
@given(st.sampled_from([case[1] for case in VALID_ISBN_CASES]))
def test_clean_isbn_is_idempotent_for_normalized_values(normalized_value: str) -> None:
    """Ensure already-normalized ISBN-13 values stay stable when re-cleaned."""

    assert clean_isbn(clean_isbn(normalized_value)) == normalized_value

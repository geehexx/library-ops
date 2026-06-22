"""Catalog-domain models for Library Ops."""

from __future__ import annotations

from contextlib import suppress
from pathlib import Path
from typing import Any, ClassVar, cast
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from PIL import Image, UnidentifiedImageError

from libraryops.catalog.managers import BibliographicWorkManager, BookEditionManager

EDITION_COVER_ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
EDITION_COVER_MAX_UPLOAD_BYTES = 5 * 1024 * 1024


def edition_cover_upload_to(instance: BookEdition, filename: str) -> str:
    """Build a stable storage path for an uploaded edition cover."""

    suffix = Path(filename).suffix.lower()
    work_id = getattr(instance, "work_id", None) or "new"
    return f"catalog/edition-covers/work-{work_id}/{uuid4().hex}{suffix}"


def validate_cover_image_size(value: Any) -> None:
    """Reject oversized cover uploads before storage writes the file."""

    size = getattr(value, "size", None)
    if size is None or size <= EDITION_COVER_MAX_UPLOAD_BYTES:
        return
    raise ValidationError(
        f"Cover images must be {EDITION_COVER_MAX_UPLOAD_BYTES // (1024 * 1024)} MB or smaller."
    )


def validate_cover_image_format(value: Any) -> None:
    """Allow only JPEG, PNG, or WebP cover uploads."""

    if value in (None, ""):
        return

    image_format = ""
    try:
        file_obj: Any = getattr(value, "file", None)
        with suppress(AttributeError):
            value.seek(0)
        with suppress(AttributeError):
            file_obj.seek(0)
        with Image.open(value) as image:
            image.verify()
            image_format = (image.format or "").upper()
    except (OSError, UnidentifiedImageError) as exc:
        raise ValidationError("Upload a JPEG, PNG, or WebP cover image.") from exc
    finally:
        file_obj = getattr(value, "file", None)
        with suppress(AttributeError):
            value.seek(0)
        with suppress(AttributeError):
            file_obj.seek(0)

    if image_format not in EDITION_COVER_ALLOWED_FORMATS:
        raise ValidationError("Upload a JPEG, PNG, or WebP cover image.")


def normalize_name(value: str) -> str:
    """Normalize text for stable equality checks."""

    return " ".join(value.strip().casefold().split())


def clean_isbn(value: str) -> str:
    """Validate and normalize an ISBN to ISBN-13 digits.

    Args:
        value: Raw ISBN input.

    Returns:
        The normalized ISBN-13 string.

    Raises:
        ValidationError: The ISBN is empty or invalid.
    """

    # ISBN-10 and ISBN-13 allow different checksum schemes; we normalize both
    # to ISBN-13 so the catalog stores one canonical representation.
    digits = "".join(ch for ch in value if ch.isdigit() or ch.upper() == "X").upper()
    if len(digits) == 10:
        # ISBN-10 uses a modulo-11 checksum where a trailing X represents 10.
        total = sum(
            (10 - index) * (10 if digit == "X" else int(digit))
            for index, digit in enumerate(digits)
        )
        if total % 11 != 0:
            raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")
        # Convert the validated ISBN-10 payload into an ISBN-13 prefix before
        # recomputing the ISBN-13 check digit.
        base = "978" + digits[:-1]
        check_total = sum(
            (1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(base)
        )
        check_digit = (10 - (check_total % 10)) % 10
        return f"{base}{check_digit}"
    if len(digits) == 13 and digits.isdigit():
        # ISBN-13 uses alternating 1/3 weights across the first 12 digits.
        total = sum(
            (1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(digits[:-1])
        )
        if (10 - (total % 10)) % 10 != int(digits[-1]):
            raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")
        return digits
    raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")


class ContributorRole(models.TextChoices):
    """Supported contributor roles for a work relation."""

    AUTHOR = "author", "Author"
    EDITOR = "editor", "Editor"
    TRANSLATOR = "translator", "Translator"
    ILLUSTRATOR = "illustrator", "Illustrator"
    OTHER = "other", "Other"


class BibliographicWork(models.Model):
    """Represent a conceptual work or title."""

    title: models.CharField[str, str] = models.CharField(max_length=255)
    normalized_title: models.CharField[str, str] = models.CharField(
        max_length=255,
        editable=False,
        db_index=True,
    )
    description: models.TextField[str, str] = models.TextField(blank=True)
    archived_at: models.DateTimeField[Any, Any] = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at: models.DateTimeField[Any, Any] = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField[Any, Any] = models.DateTimeField(auto_now=True)

    objects: ClassVar[BibliographicWorkManager] = BibliographicWorkManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        """Default ordering for catalog works."""

        ordering = ("title",)

    def __str__(self) -> str:
        """Return a human-readable work label."""

        return self.title

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the work with normalized search text."""

        self.normalized_title = normalize_name(self.title)
        super().save(*args, **kwargs)

    @property
    def available_copy_count(self) -> int:
        """Return the number of active copies currently available."""

        return self._copy_count_for_status("available")

    @property
    def on_loan_copy_count(self) -> int:
        """Return the number of active copies currently on loan."""

        return self._copy_count_for_status("on_loan")

    def _copy_count_for_status(self, status: str) -> int:
        """Count active copies for one status across prefetched editions."""

        return sum(
            1
            for edition in cast("Any", self).editions.all()
            for copy in edition.copies.all()
            if copy.archived_at is None and copy.status == status
        )


class Contributor(models.Model):
    """Represent a contributor identity reused across works."""

    name: models.CharField[str, str] = models.CharField(max_length=255)
    normalized_name: models.CharField[str, str] = models.CharField(
        max_length=255,
        editable=False,
        unique=True,
    )
    created_at: models.DateTimeField[Any, Any] = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Default ordering for contributor rows."""

        ordering = ("name",)

    def __str__(self) -> str:
        """Return a human-readable contributor label."""

        return self.name

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the contributor with normalized equality text."""

        self.normalized_name = normalize_name(self.name)
        super().save(*args, **kwargs)


class WorkContributor(models.Model):
    """Link a work and contributor with a role and display order."""

    work: models.ForeignKey[BibliographicWork, BibliographicWork] = models.ForeignKey(
        BibliographicWork,
        on_delete=models.CASCADE,
        related_name="work_contributors",
    )
    contributor: models.ForeignKey[Contributor, Contributor] = models.ForeignKey(
        Contributor,
        on_delete=models.CASCADE,
        related_name="work_contributors",
    )
    role: models.CharField[str, str] = models.CharField(
        max_length=32,
        choices=ContributorRole.choices,
    )
    sort_order: models.PositiveIntegerField[int, int] = models.PositiveIntegerField(default=0)

    class Meta:
        """Default ordering and uniqueness for work-contributor links."""

        ordering = ("sort_order", "id")
        constraints = (
            models.UniqueConstraint(
                fields=["work", "contributor", "role"],
                name="unique_work_contributor_role",
            ),
        )

    def __str__(self) -> str:
        """Return a human-readable relation label."""

        return f"{self.work} / {self.contributor} ({self.role})"


class BookEdition(models.Model):
    """Represent an edition or publication record for a work."""

    work: models.ForeignKey[BibliographicWork, BibliographicWork] = models.ForeignKey(
        BibliographicWork,
        on_delete=models.PROTECT,
        related_name="editions",
    )
    publisher: models.CharField[str, str] = models.CharField(max_length=255, blank=True)
    publication_year: models.PositiveIntegerField[int | None, int | None] = (
        models.PositiveIntegerField(
            blank=True,
            null=True,
        )
    )
    language: models.CharField[str, str] = models.CharField(max_length=16, default="en")
    isbn: models.CharField[str | None, str | None] = models.CharField(
        max_length=13,
        blank=True,
        unique=True,
        null=True,
    )
    cover_url: models.URLField[str, str] = models.URLField(blank=True)
    cover_image: models.ImageField = models.ImageField(
        blank=True,
        null=True,
        upload_to=edition_cover_upload_to,
        validators=[validate_cover_image_size, validate_cover_image_format],
    )
    description: models.TextField[str, str] = models.TextField(blank=True)
    external_identifiers: models.JSONField[dict[str, object], dict[str, object]] = models.JSONField(
        default=dict,
        blank=True,
    )
    archived_at: models.DateTimeField[Any, Any] = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at: models.DateTimeField[Any, Any] = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField[Any, Any] = models.DateTimeField(auto_now=True)
    objects: ClassVar[BookEditionManager] = BookEditionManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    class Meta:
        """Default ordering for edition rows."""

        ordering = ("work__title", "publication_year", "id")

    def __str__(self) -> str:
        """Return a human-readable edition label."""

        return f"{self.work} ({self.isbn or 'no-isbn'})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the edition after validation."""

        # Normalize ISBN before field validation so raw 10-digit inputs can
        # expand to ISBN-13 before Django enforces max_length.
        self.clean()
        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Normalize and validate model fields before persistence."""

        if self.isbn:
            self.isbn = clean_isbn(self.isbn)

    @property
    def cover_preview_url(self) -> str | None:
        """Return the best available cover preview URL for UI consumption."""

        if self.cover_image:
            try:
                return self.cover_image.url
            except ValueError:
                return None
        return self.cover_url or None


class ExternalSourceRecord(models.Model):
    """Track imported-data provenance for work or edition targets."""

    source_name: models.CharField[str, str] = models.CharField(max_length=64)
    source_identifier: models.CharField[str, str] = models.CharField(max_length=255)
    source_url: models.URLField[str, str] = models.URLField(blank=True)
    license_note: models.CharField[str, str] = models.CharField(max_length=255, blank=True)
    work: models.ForeignKey[BibliographicWork | None, BibliographicWork | None] = models.ForeignKey(
        BibliographicWork,
        on_delete=models.CASCADE,
        related_name="source_records",
        blank=True,
        null=True,
    )
    edition: models.ForeignKey[BookEdition | None, BookEdition | None] = models.ForeignKey(
        BookEdition,
        on_delete=models.CASCADE,
        related_name="source_records",
        blank=True,
        null=True,
    )
    imported_at: models.DateTimeField[Any, Any] = models.DateTimeField(default=timezone.now)
    fetched_at: models.DateTimeField[Any, Any] = models.DateTimeField(default=timezone.now)

    class Meta:
        """Default ordering and uniqueness for provenance rows."""

        ordering = ("source_name", "source_identifier")
        constraints = (
            models.UniqueConstraint(
                fields=["source_name", "source_identifier"],
                name="unique_source_identifier",
            ),
        )

    def __str__(self) -> str:
        """Return a human-readable provenance label."""

        return f"{self.source_name}:{self.source_identifier}"

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the provenance record after validation."""

        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Ensure provenance records target exactly one catalog object."""

        if (self.work is None) == (self.edition is None):
            raise ValidationError(
                "External source records must point to exactly one work or edition."
            )

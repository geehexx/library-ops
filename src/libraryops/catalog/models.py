"""Catalog-domain models for Library Ops."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, ClassVar

from django.contrib.auth.models import Group, User
from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Prefetch
from django.utils import timezone
from guardian.shortcuts import assign_perm

from libraryops.accounts.roles import iter_role_definitions
from libraryops.audit.services import record_audit_event
from libraryops.inventory.models import BookCopy, BookCopyStatus


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

    digits = "".join(ch for ch in value if ch.isdigit() or ch.upper() == "X").upper()
    if len(digits) == 10:
        total = sum(
            (10 - index) * (10 if digit == "X" else int(digit))
            for index, digit in enumerate(digits)
        )
        if total % 11 != 0:
            raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")
        base = "978" + digits[:-1]
        check_total = sum(
            (1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(base)
        )
        check_digit = (10 - (check_total % 10)) % 10
        return f"{base}{check_digit}"
    if len(digits) == 13 and digits.isdigit():
        total = sum(
            (1 if index % 2 == 0 else 3) * int(digit) for index, digit in enumerate(digits[:-1])
        )
        if (10 - (total % 10)) % 10 != int(digits[-1]):
            raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")
        return digits
    raise ValidationError("Enter a valid ISBN-10 or ISBN-13 value.")


@dataclass(frozen=True, slots=True)
class CatalogFoundationData:
    """Validated input for the Phase 1 catalog create flow."""

    title: str
    contributor_name: str
    contributor_role: str
    isbn: str
    barcode: str
    publisher: str
    publication_year: int | None
    language: str
    shelf_location: str


class ContributorRole(models.TextChoices):
    """Supported contributor roles for a work relation."""

    AUTHOR = "author", "Author"
    EDITOR = "editor", "Editor"
    TRANSLATOR = "translator", "Translator"
    ILLUSTRATOR = "illustrator", "Illustrator"
    OTHER = "other", "Other"


class BibliographicWorkQuerySet(models.QuerySet["BibliographicWork"]):
    """Query helpers for foundation catalog views."""

    def active(self) -> BibliographicWorkQuerySet:
        """Return only non-archived works."""

        return self.filter(archived_at__isnull=True)

    def with_foundation_graph(self) -> BibliographicWorkQuerySet:
        """Prefetch the related foundation graph for evaluator-facing pages."""

        contributor_queryset = WorkContributor.objects.select_related("contributor").order_by(
            "sort_order",
            "id",
        )
        edition_queryset = BookEdition.objects.prefetch_related("copies")
        return self.prefetch_related(
            Prefetch("work_contributors", queryset=contributor_queryset),
            Prefetch("editions", queryset=edition_queryset),
        )


class BibliographicWorkManager(models.Manager["BibliographicWork"]):
    """Own write orchestration and read-optimized catalog query helpers."""

    def get_queryset(self) -> BibliographicWorkQuerySet:
        """Return the project queryset with catalog-specific helpers."""

        return BibliographicWorkQuerySet(self.model, using=self._db)

    def foundation_index(self) -> BibliographicWorkQuerySet:
        """Return the read-optimized queryset for foundation pages."""

        return self.get_queryset().with_foundation_graph().active()

    @transaction.atomic
    def create_foundation_record(
        self,
        *,
        actor: User,
        data: CatalogFoundationData,
    ) -> BibliographicWork:
        """Create the Phase 1 work, contributor, edition, copy, and audit event atomically."""

        work = self.create(title=data.title)
        contributor, _ = Contributor.objects.get_or_create(
            normalized_name=normalize_name(data.contributor_name),
            defaults={"name": data.contributor_name},
        )
        WorkContributor.objects.create(
            work=work,
            contributor=contributor,
            role=data.contributor_role,
        )
        edition = BookEdition.objects.create(
            work=work,
            isbn=data.isbn,
            publisher=data.publisher,
            publication_year=data.publication_year,
            language=data.language,
        )
        copy = BookCopy.objects.create(
            edition=edition,
            barcode=data.barcode,
            shelf_location=data.shelf_location,
            status=BookCopyStatus.AVAILABLE,
        )
        self._assign_object_permissions(work, edition, copy)
        record_audit_event(
            actor=actor,
            action="catalog.foundation.create",
            target=work,
            metadata={
                "edition_id": edition.pk,
                "copy_id": copy.pk,
                "contributor_id": contributor.pk,
            },
        )
        return work

    def _assign_object_permissions(self, *objects: models.Model) -> None:
        """Grant object permissions to the committed role groups."""

        for role_definition in iter_role_definitions():
            for group in Group.objects.filter(name=role_definition.name):
                for obj in objects:
                    for permission_name in role_definition.object_permissions:
                        permission_app_label, permission_codename = permission_name.split(
                            ".",
                            maxsplit=1,
                        )
                        if permission_app_label != obj._meta.app_label:
                            continue
                        model_name = obj._meta.model_name or ""
                        if not permission_codename.endswith(model_name):
                            continue
                        assign_perm(permission_codename, group, obj)


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

    class Meta:
        """Default ordering for edition rows."""

        ordering = ("work__title", "publication_year", "id")

    def __str__(self) -> str:
        """Return a human-readable edition label."""

        return f"{self.work} ({self.isbn or 'no-isbn'})"

    def save(self, *args: object, **kwargs: object) -> None:
        """Persist the edition after validation."""

        self.full_clean()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Normalize and validate model fields before persistence."""

        if self.isbn:
            self.isbn = clean_isbn(self.isbn)


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

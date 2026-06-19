"""Inventory models for borrowable copies."""

from __future__ import annotations

from datetime import datetime  # noqa: TC003
from typing import Any, ClassVar, cast

from django.contrib.auth.models import User  # noqa: TC002
from django.core.exceptions import PermissionDenied
from django.db import models, transaction
from django.utils import timezone

from libraryops.accounts.roles import CATALOG_CREATE_PERMISSIONS
from libraryops.audit.models import AuditEvent


class BookCopyStatus(models.TextChoices):
    """Supported inventory statuses for a copy."""

    AVAILABLE = "available", "Available"
    ON_LOAN = "on_loan", "On loan"
    MAINTENANCE = "maintenance", "Maintenance"
    LOST = "lost", "Lost"
    ARCHIVED = "archived", "Archived"


def _require_catalog_manager(actor: User) -> None:
    """Reject users that cannot manage catalog records."""

    if not actor.is_authenticated or not actor.has_perms(CATALOG_CREATE_PERMISSIONS):
        raise PermissionDenied("Catalog mutations require librarian or admin access.")


def _changed_fields(
    before: dict[str, object],
    after: dict[str, object],
) -> dict[str, dict[str, object]]:
    """Return a compact field-change payload."""

    changes: dict[str, dict[str, object]] = {}
    for key, new_value in after.items():
        old_value = before.get(key)
        if old_value == new_value:
            continue
        changes[key] = {"from": old_value, "to": new_value}
    return changes


class BookCopyManager(models.Manager["BookCopy"]):
    """Own copy CRUD and archive logic."""

    @transaction.atomic
    def create_copy(
        self,
        *,
        actor: User,
        edition: models.Model,
        barcode: str,
        status: BookCopyStatus | str = BookCopyStatus.AVAILABLE,
        shelf_location: str = "",
        condition_note: str = "",
    ) -> BookCopy:
        """Create one copy and record the mutation."""

        _require_catalog_manager(actor)
        copy = self.create(
            edition=edition,
            barcode=barcode,
            status=BookCopyStatus(status),
            shelf_location=shelf_location,
            condition_note=condition_note,
        )
        AuditEvent.objects.record_event(
            actor=actor,
            action="catalog.copy.create",
            target=copy,
            metadata=copy.audit_state(),
        )
        return copy

    @transaction.atomic
    def update_copy(
        self,
        *,
        actor: User,
        copy: BookCopy,
        edition: models.Model | None = None,
        barcode: str | None = None,
        status: BookCopyStatus | str | None = None,
        shelf_location: str | None = None,
        condition_note: str | None = None,
    ) -> BookCopy:
        """Update one copy and record the mutation."""

        _require_catalog_manager(actor)
        if copy.pk is None:
            raise ValueError("Cannot update an unsaved copy.")
        copy = self.get(pk=copy.pk)
        before = copy.audit_state()
        copy.apply_updates(
            edition=edition,
            barcode=barcode,
            status=status,
            shelf_location=shelf_location,
            condition_note=condition_note,
        )
        after = copy.audit_state()
        changes = _changed_fields(before, after)
        if changes:
            copy.save()
            AuditEvent.objects.record_event(
                actor=actor,
                action="catalog.copy.update",
                target=copy,
                metadata={"changes": changes},
            )
        return copy

    @transaction.atomic
    def archive_copy(self, *, actor: User, copy: BookCopy) -> BookCopy:
        """Archive one copy and record the mutation."""

        _require_catalog_manager(actor)
        if copy.pk is None:
            raise ValueError("Cannot archive an unsaved copy.")
        copy = self.get(pk=copy.pk)
        if copy.archived_at is None or copy.status != BookCopyStatus.ARCHIVED.value:
            archived_at = copy.archived_at or timezone.now()
            copy.mark_archived(archived_at=archived_at)
            copy.save()
            AuditEvent.objects.record_event(
                actor=actor,
                action="catalog.copy.archive",
                target=copy,
                metadata={
                    "archived_at": archived_at.isoformat(),
                    "status": str(copy.status),
                },
            )
        return copy


class BookCopy(models.Model):
    """Represent a borrowable copy attached to an edition."""

    edition: models.ForeignKey[models.Model, models.Model] = models.ForeignKey(
        "catalog.BookEdition", on_delete=models.PROTECT, related_name="copies"
    )
    barcode: models.CharField[str, str] = models.CharField(max_length=64, unique=True)
    status: models.CharField[str, str] = models.CharField(
        max_length=32,
        choices=BookCopyStatus.choices,
        default=BookCopyStatus.AVAILABLE,
    )
    shelf_location: models.CharField[str, str] = models.CharField(max_length=64, blank=True)
    condition_note: models.TextField[str, str] = models.TextField(blank=True)
    archived_at: models.DateTimeField[datetime | None, datetime | None] = models.DateTimeField(
        blank=True,
        null=True,
    )
    created_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now_add=True)
    updated_at: models.DateTimeField[datetime, datetime] = models.DateTimeField(auto_now=True)

    class Meta:
        """Default ordering for book copies."""

        ordering = ("barcode",)

    objects: ClassVar[BookCopyManager] = BookCopyManager()  # pyright: ignore[reportIncompatibleVariableOverride]

    def __str__(self) -> str:
        """Return a human-readable copy label."""

        return self.barcode

    def audit_state(self) -> dict[str, object]:
        """Return the mutable state tracked in audit payloads."""

        edition_id = cast(Any, self).edition_id
        return {
            "edition_id": edition_id,
            "barcode": self.barcode,
            "status": self.status,
            "shelf_location": self.shelf_location,
            "condition_note": self.condition_note,
        }

    def apply_updates(
        self,
        *,
        edition: models.Model | None = None,
        barcode: str | None = None,
        status: BookCopyStatus | str | None = None,
        shelf_location: str | None = None,
        condition_note: str | None = None,
    ) -> None:
        """Apply in-memory field updates before persistence."""

        if edition is not None:
            self.edition = edition
        if barcode is not None:
            self.barcode = barcode
        if status is not None:
            self.status = BookCopyStatus(status)
        if shelf_location is not None:
            self.shelf_location = shelf_location
        if condition_note is not None:
            self.condition_note = condition_note

    def mark_archived(self, *, archived_at: datetime) -> None:
        """Move the copy into the archived state."""

        self.status = BookCopyStatus.ARCHIVED.value
        self.archived_at = archived_at
